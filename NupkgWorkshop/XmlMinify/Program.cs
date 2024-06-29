using System.Xml;

namespace XmlMinify
{
    public class Program
    {
        static void Main(string[] args)
        {
            if (args.Length != 2)
            {
                Console.WriteLine("Usage: XmlMinifier <input file or directory> <output file or directory>");
                return;
            }

            string inputPath = args[0];
            string outputPath = args[1];

            if (Directory.Exists(inputPath))
            {
                if (!Directory.Exists(outputPath))
                {
                    Directory.CreateDirectory(outputPath);
                }

                ProcessDirectory(inputPath, outputPath);
            }
            else if (File.Exists(inputPath) && !Directory.Exists(outputPath))
            {
                ProcessFile(inputPath, outputPath);
            }
            else
            {
                Console.WriteLine("Invalid input or output path.");
            }
        }

        static void ProcessDirectory(string inputDir, string outputDir)
        {
            foreach (string inputFile in Directory.GetFiles(inputDir, "*", SearchOption.AllDirectories))
            {
                string relativePath = Path.GetRelativePath(inputDir, inputFile);
                string outputFile = Path.Combine(outputDir, relativePath);

                Directory.CreateDirectory(Path.GetDirectoryName(outputFile));

                ProcessFile(inputFile, outputFile);
            }
        }

        static void ProcessFile(string inputFile, string outputFile)
        {
            if (IsXmlFile(inputFile))
            {
                using FileStream inputFileStream = new(inputFile, FileMode.Open, FileAccess.Read);
                using FileStream outputFileStream = new(outputFile, FileMode.Create, FileAccess.Write);
                using StreamWriter writer = new(outputFileStream);

                string minifiedXml = Minify(inputFileStream);
                writer.Write(minifiedXml);
            }
            else
            {
                File.Copy(inputFile, outputFile, true);
            }
        }

        static bool IsXmlFile(string filePath)
        {
            using StreamReader reader = new(filePath);
            int firstChar = reader.Read();
            return firstChar == '<';
        }

        public static string Minify(Stream input)
        {
            XmlDocument doc = new();
            doc.Load(input);

            using MemoryStream memoryStream = new MemoryStream();
            using XmlWriter writer = XmlWriter.Create(memoryStream, new XmlWriterSettings { Indent = false, OmitXmlDeclaration = true });


            doc.Save(writer);
            writer.Flush();

            // Remove BOM
            byte[] temp = memoryStream.ToArray();
            byte[] noBom = temp.SkipWhile(c => c != '<').ToArray();

            // Remove space before self-closing tags
            // <Task /> ---to---> <Task/>
            string tempStr = System.Text.Encoding.UTF8.GetString(noBom);
            tempStr = tempStr.Replace(" />", "/>");

            return tempStr;
        }
    }

}
