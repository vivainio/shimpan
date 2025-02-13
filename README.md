# shimpan

Create exe shims easily. Never modify your PATH again!

Can create 2 types of shims, ['scoop'](https://github.com/ScoopInstaller/Shim) shim is built on .NET and ['alt'](https://github.com/71/scoop-better-shimexe) is C.

You can use it as a lightweight way to publish your app without using Scoop, Chocolatey or Winget.

An example from [Heymars}(https://github.com/vivainio/heymars) application (that was maybe too niche for me to bother packaging to Scoop or Winget):

```
uvx shimpan get https://github.com/vivainio/heymars/releases/download/v1.2.1/heymars-1.2.1.zip --to ~/.local/bin
```

This Unzips it to  USER\AppData\Local\Programs\heymars-1.2.1 and creates .exe shim to ~/.local/bin (which is likely in the path if you have uv installed).
