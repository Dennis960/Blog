---
title: "Cmd test disk speed on Windows"
date: 2021-02-24T11:08:26+01:00
image: Hard-Drive.jpg
draft: false
---

Today I learned how to test the disk speed on Windows using cmd commands. It is the easiest process as it is just a single command but I needed to look it up twice already.
That is why I decided to make this blog post so that I could easily find the command next time I need it.
![Command snippet](CmdTestDiskSpeed.svg)
Run it as admin so it doesn't open another terminal.  
winsat disk -seq -write -drive c  
winsat disk -seq -read -drive c  
The first line tests the write speed and the second one tests the read speed. The c stands for the disk that should be tested. The output looked like this:
![example output](CmdDiskSpeedOutput.svg)
My SSD therefore has a write speed of 243.54 MB/s