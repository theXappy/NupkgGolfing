This is a writeup of my `.nupkg` golfing process for BGGP 5.

## Abstract
This year, BGGP 5's theme is "Download".
The goal is fetching the file over at `https://binary.golf/5/5` and showing its content on the screen.  
I wanted to do something .NET related but C# is only valid as a PE executable (and the C/assembly gang is going to win that one).  
I vaugely recalled the cool research of [IAmRoot by C. Augusto Proiete](https://github.com/augustoproiete/i-am-root-nuget-package), which lets you run code once a 'malicious' nuget package is installed.  
So we're targeting Visual Studio's nuget client :)

## Submitted Artifact
The submitted `.nupkg` file consists of 3 'formats', each needed to be golf'd:
1. A C# expression (This is the actual done to download + show the `5` file)
2. Two XML files. One of them contains the C# expr.
3. A Zip file containing both XML files.

![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/67a90b81-8ae4-4994-a218-4fd41258ee6d)

## The Plan
Nuget packages are stored (on the nuget server) and served to VisualStudio as `.nupkg` files.  
My plan was start from a slightly modified IAmRoot's nupkg and inclementally trim parts of it.  
`.nupkg` files are just fancy `.zip` files (as Microsoft loves to do. Hey `.docx`!).  
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/eab4a177-f3b9-4ec3-9a18-90850691a4f7)

I figured I'm going to edit the files inside **constantly** then `zip`'em and "add" the package to my local nuget repository.  
Lucky me, the bikeshedding was short and finite and within an hour I got a custom working "Nupkg Workbench" working in Visual Studio Code.  
This allows me to modify the extracted files from the zip and with a few clicks run a "Task" that automatically zips the files and update the repo with the new nupkg.  
This workspace is documented in the "Nupkg Workbench" directory in this repo. 
(*You'll need to tweak some paths in `.vscode/tasks.json` to make things work on your machine)

## The Golfing Process
### 1. Cloned IAmRoot
After cloning I made sure with Visaul Studio, configured with a local nuget feed, that the code execution wasn't "patched" yet (Not sure if MS is even going to).

### 2. Golfing the C# Expression
First I had to modify the "IAmRoot" source to do the BGGP file download + displaying the results
This was done by editing the `build/IAmRoot.targets` file. It had embedded C# code to show the original groot image:
```C#
<Using Namespace="System" />
<Using Namespace="System.Diagnostics" />
<Code Type="Fragment" Language="cs"><![CDATA[
try
{
	ProcessStartInfo startInfo = new ProcessStartInfo();
	startInfo.FileName = "https://raw.githubusercontent.com/augustoproiete/i-am-root-nuget-package/master/assets/i-am-root.jpg";
	startInfo.UseShellExecute = true;
	Process process = new Process();
	process.StartInfo = startInfo;
	process.Start();
}
catch(Exception ex)
{
    Log.LogError(ex.Message);
}
]]></Code>
```
I modified it to this:
```C#
<Code>Log.LogError(new System.Net.WebClient().DownloadString("https://binary.golf/5/5"));</Code>
```
Notice that I was able to drop the `<![CDATA[...]]>` syntax since my single line doesn't have any characters that can be interepreted differently by a XML reader.

### 3. Golfing the `.nupkg` Content
Just like any other `.nupkg`, IAmRoot's `.nupkg` contained multiple folders and files.  
I suspected some of them are redundant so I progressively removed them and checked if `nuget.exe` and Visual Studio that re-constructed `.nupkg`s still behave as expected.

![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/de481566-aa5c-4b2d-a67c-e705898bdad9)

As you can see, the minimal required structure is much smaller. Consisting of just 1 directory and 2 files.  
1. The `.nuspec` files declares information about the packge: Name, version, Developer etc. It's mandatory in every `.nupkg`.
2. The `.targets` files is the actually an optional file but this is where we exploit the build event to trigger our download, so for our case we must have it.

Both files are actually **xml files**.

### 4. Golfing the XMLs
This step splits into 2 smaller parts:

#### 4.1. Golfing the XML content
Just like with the zip structure, I suspected many properties and namespaces are either useless or `nuget.exe`/Visual Studio can work without them (assuming default values).  
I managed to trim quite a lot of bytes from each.
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/91ff14d2-0e61-472b-b564-3406f5b8ffb9)
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/172a725d-da92-4676-8606-6e91cc68446b)

An interesting anacdote about `.nuspec`:  
The root `<package>` node doesn't have to be a "package", anything will work and I used `<m>` (to try and squeeze some overlap with `<metadata`, for the compression algorithm).  
I bet the XML parsing logic just accesses the first non-`<xml>` node in the file.  
This doesn't work on the inner `<metadata>` tag. Changing it to anything causes `nuget.exe` to complain.

#### 4.2. Minifying the XMLs
Obviously, I could just remove whitespaces and newlines in my working copies of the XML.  
But that makes modifying them a pain in the ass. So Instead I just added an automatic "build" step that minifies the XMLs before shoving them into the zip.  
For Example:
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/0913fdb8-5675-4449-86c5-1fb633558d62)

This was done with a very simple C# program I called `XmlMinify`. Its code is also present in this repo.

### 5. Golfing the Zip Binary Format
As mentioned, `.nupkg` is just a zip file. So once we zip both XMLs we still need to optimize the zip representation.  
I found this nice tool called [FileOptimizer](https://nikkhokkho.sourceforge.io/?page=FileOptimizer) by Javier Gutiérrez Chamorro.  
And I was also told about [amadvance/advancecomp](https://github.com/amadvance/advancecomp), which I think FileOptimizer uses it behind the scenes.  
Anyway both got me to a super slim .zip but they were re-compressing with a format not supported by .NET `ZipArchive` class. It only support DEFLATE(64)/No compression:
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/6b11c599-6e11-4f58-b746-ab59bc687007)

So I compressed with DEFLATE (and the maximum compression settings for 7zip, `-mx=9`) and manually modified the output.  

Manual zip modifications:
1. 7zip creates zip entries for files and folders. Folders existance can be implied from an innter file/folder so you can omit the folder's entry.
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/699fddc9-e87f-4951-9296-516f7c513178)
2. 7zip creates both a "Dir Entry" and a "File Record" for every file. Both have a "name" field.
   Seemed redundant to me and I was happy to discover .NET's/VS's zip decompressor can work with just one of them:
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/265634ce-09af-4a2e-91c0-cb2a3777f83f)
3. Remove the "extra" data fields from both "Dir Entries" that were left.
4. Finally, fix all pointers/sizes:
     1. Each "Dir Entry" has a pointer to the "File Record" the first one (still) pointed to the record at 0 so I only had to fix the second one.
     2. The footer has a pointer to the first "Dir Entry" in the root directory.
     3. The footer has the total size of all entries in the root directory.
     4. The footer has 2 "amount of entries" fields, one is "entries in this zip" and the other is "entries in total" (for split zips?). I had to fix both from 3 to 2 since I removed the folder's entry.
![image](https://github.com/theXappy/NupkgGolfing/assets/10898152/91e8635c-c4cc-4b65-8282-57c1184a6504)


And that's it!
The final result is:
```
a.nupkg (zip) size: 491 bytes
(
Out of which:
  1. The decompressed XML sizes: 79 + 332 = 411 bytes
  2. C# Expresion: 83 bytes
)
```

