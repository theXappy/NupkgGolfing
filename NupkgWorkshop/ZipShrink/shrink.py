import struct
import sys
import zipfile

trim_enabled = "--no-trim" not in sys.argv
if len(sys.argv) < 3 or "--help" in sys.argv or "-h" in sys.argv:
    print("Usage: shrink.py [--no-trim] INPUT_PATH OUTPUT_PATH")
    sys.exit(1)
input_path = sys.argv[-2]
output_path = sys.argv[-1]

def parse_zip(file_path):
    with open(file_path, 'rb') as f:
        f.seek(0, 2)
        print("Input size: ", f.tell())
        f.seek(-22, 2)
        end_of_central_dir = f.read(22)
        endMarkerSignature, disk_num, disk_with_cd, num_entries_disk, num_entries, cd_size, cd_offset, comment_len = struct.unpack('<IHHHHIIH', end_of_central_dir)

        dir_entries = []

        final_shrinked_zip = b''

        f.seek(cd_offset)
        for _ in range(num_entries):
            dir_ent = f.read(46)
            (
                signature, ver, ver_needed, 
                flags, comp_method, mod_time, 
                mod_date, crc, comp_size, 
                uncomp_size, filename_len, 
                extra_len, comment_len, 
                disk_num_start, internal_attr, ext_attr, 
                header_off 
            ) = struct.unpack('<IHHHHHHIIIHHHHHII', dir_ent)
            
            filename = f.read(filename_len)
            extra = f.read(extra_len)
            comment = f.read(comment_len)
            
            current_position = f.tell()
            f.seek(header_off)
            file_record_header = f.read(30)

            # Unpack the fixed part of the file record
            (
                frSignature, frVersion, frFlags, frCompression,
                frFileTime, frFileDate, frCrc, frCompressedSize,
                frUncompressedSize, frFileNameLength, frExtraFieldLength
            ) = struct.unpack('<4sHHHHHIIIHH', file_record_header)

            # Read the variable-length fields
            frFileName = f.read(frFileNameLength)
            frExtraField = f.read(frExtraFieldLength)
            frData = f.read(frCompressedSize)

            # Jump back to central directory parsing
            f.seek(current_position)
            
            file_record_old = file_record_header + frFileName + frExtraField + frData

            if trim_enabled:
                frFileName = b''
                frExtraField = b''

            # Encode the fixed part of the file record
            file_header = struct.pack(
                '<4sHHHHHIIIHH',
                frSignature, frVersion, frFlags, frCompression,
                frFileTime, frFileDate, frCrc, frCompressedSize,
                frUncompressedSize, len(frFileName), len(frExtraField)
            )

            # Combine everything to form the complete file record
            file_record_new = file_header + frFileName + frExtraField + frData

            is_directory = filename.decode().endswith("/")
            # Skip entries representing directories if trimming
            if trim_enabled and is_directory:
                pass
            else:
                new_header_off = len(final_shrinked_zip)
                final_shrinked_zip += file_record_new

                if trim_enabled:
                    extra = b''
                    comment = b''

                dir_ent = struct.pack(
                    '<IHHHHHHIIIHHHHHII',
                    signature, ver, ver_needed, flags, comp_method, mod_time, mod_date, crc, 
                    comp_size, uncomp_size, filename_len, len(extra), len(comment), 
                    disk_num_start, internal_attr, ext_attr, new_header_off
                )
                dir_ent = dir_ent + filename + extra + comment

                dir_entries.append(dir_ent)

        central_dir_off = len(final_shrinked_zip)
        total_size_central_dir = 0
        for dir_entry in dir_entries:
            total_size_central_dir += len(dir_entry)
            final_shrinked_zip += dir_entry

        end_of_central_dir = struct.pack(
            '<IHHHHIIH',
            endMarkerSignature, disk_num, disk_with_cd, 
            len(dir_entries),  # Modified
            len(dir_entries),  # Modified
            total_size_central_dir,  # Modified
            central_dir_off,  # Modified
            comment_len
        )
        final_shrinked_zip += end_of_central_dir

        print("Final zip size: ", len(final_shrinked_zip))
        return final_shrinked_zip


shrinked_bytes = parse_zip(input_path)
fd = open(output_path, "wb")
fd.write(shrinked_bytes)
fd.close()
