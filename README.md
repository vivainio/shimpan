# shimpan

Create exe shims easily. Never modify your PATH again!

Can create 2 types of shims, ['scoop'](https://github.com/ScoopInstaller/Shim) shim is built on .NET and ['alt'](https://github.com/71/scoop-better-shimexe) is C.

# Installation

```
pip install shimpan
```

But of course you have installed Uv and can run it with uvx:

```
$ uvx shimpan --help
usage: shimpan [-h] [--shim {alt,scoop}] [--to TO] {create,get} ...

Shimpan: Create shims for exes that are in path. Version: 1.3.0

positional arguments:
  {create,get}
    create            Create a shim for an executable. The lowest level action
    get               Download zip file, install it as an application

options:
  -h, --help          show this help message and exit
  --shim {alt,scoop}  Shim type. Default is 'scoop'
  --to TO             The directory where the shim files (.exe, .shim) will be created
```

## Creating shims

To create shims, just call "shimpan create". Here I create a shim to pgadmin:

```
$ shimpan --to \r\myapps create "C:\Users\villevai\AppData\Local\Programs\pgAdmin 4\runtime\pgAdmin4.exe"
Shims (.exe, .shim) created at \r\myapps\pgAdmin4.exe pointing to C:\Users\villevai\AppData\Local\Programs\pgAdmin 4\runtime\pgAdmin4.exe
```

After this, I can see the files in target directory:

```
❯ ls pgAdmin*

    Directory: C:\r\myapps

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          13/02/2025    21.07           9728 pgAdmin4.exe
-a---          13/02/2025    21.07             80 pgAdmin4.shim
```

This is something you can easily have on your PATH.

The shim file itself looks like this:

```
$ cat .\pgAdmin4.shim
path = C:\Users\villevai\AppData\Local\Programs\pgAdmin 4\runtime\pgAdmin4.exe
```

Calling pgAdmin4.exe reads the shim file and executes the pointed executable. 

## Easy installation of third party apps

You can use Shimpan as a lightweight way to publish your app without using Scoop, Chocolatey or Winget.

An example from [Heymars](https://github.com/vivainio/heymars) application (that was maybe too niche for me to bother packaging to Scoop or Winget):

```
uvx shimpan get https://github.com/vivainio/heymars/releases/download/v1.2.1/heymars-1.2.1.zip --to ~/.local/bin
```

This Unzips it to  USER\AppData\Local\Programs\heymars-1.2.1 and creates .exe shim *for every .exe file in the zip* to ~/.local/bin (which is likely in the path already if you have uv installed).

If you omit the --to argument, it creates the shims in current directory. You can then try it copy them wherever you want (probably some nice place on your PATH).
The shims don't care where they are, they only care about where the .shim file points at.

### What's deal with the name?

I planned to call it Shimpanz or Shimpans, but that would have been gringe. Henge Shimpan.

