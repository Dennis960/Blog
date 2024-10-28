---
title: "Day Structure Project"
date: 2021-02-26T22:33:54+01:00
image: overthinkingPerson.jpg
draft: false
---

Planning my day was one of the most difficult tasks for me. It was the same problem almost every day. I only get out of bed very late and by the time I do I have already missed the time to eat breakfast. In the morning I spent most of my time scrolling through Instagram, YouTube or watching Netflix. The worst part about that wasn't even the amount of time I wasted by doing absolutely nothing but rather the uncomfortable position in which I was sitting in my bed. Only a few minutes in and my back was already hurting but I was just too lazy to stand up and get ready for the day.

I knew that I had to change something about my lifestyle. I needed some kind of structure in my days. I always thought about using my Sunday evening to plan out my entire week. I wanted to plan every last minute to be as productive as possible and also to have a goal. The only problem I was facing every time I had these thoughts were all the spontaneous appointments and especially my school homework for which I never knew how long it would take me. I also had to plan in time to eat breakfast, lunch and dinner but these things would always happen at a different time depending on the rest of my family. Therefore a fixed schedule wouldn't work. I needed something dynamic, something that would adjust every second and every time I needed to add a new task or a new appointment. It would need to dynamically change whenever I finished a task early or needed more time.

So I made a plan. Most of the times when I make plans I am not able to stick to it in the way I want to. But this time I just had to. If I finish this project it will change my entire life and my productivity may go up enormously.

As you may know I am a programmer. I love to code and I love to develop complicated and complex software. It must be either visually looking amazing or it has to be a text-mess that nobody except me will ever come near to understand. This time I chose the first option though as I am a really bad artist and a really bad designer, reusing applications made by other people would be my best option. I am currently planning my days with the help of Google Calendar and the todo list app called Trello. With the help of python I wanted to combine these two and automate the process of adding Trello tasks to the Google Calendar. My plan was as follows:

- Put all the projects, appointments and tasks into a Trello Todo-List
- Give each task:
  - An amount of time needed
  - A priority
  - A due date
  - A label (sport, free-time, school, friends, social media and so on)
  - (A transition time between events)
- A python script would run on my raspberry pi that is connected to the Internet
- Whenever I change, add or delete a todo item from Trello it would automatically update my Google Calendar
- The tasks should be evenly spread and I wouldn't have to do all my school homework in a row
- There would be enough breaks in between the tasks where I would read a book, watch a movie or just breath and live

All in all my plan sounded really nice and I immediately started development.

### Development
Both the Google Calendar and the Trello app have an API that can be used in python. After some research on Google I used
![pip commands](/images/pipCalendarTrello.svg)
With the help of the quick-start tutorial I got my first script up and running and was able to access the calendar linked to my google account. I was worried that I would accidentally destroy my current calendar so I used a different G-Mail address for this project. After a bit of toying around I was able to
- delete all events from the calendar
- add an event
- remove a specific event
- change the color of events
- adjust the time and duration
- find a spot in between events that would fit another event with a given duration

The last aspect was the most important one. It would give me the ability to fit events in between fixed timestamps. The next thing I had to do was access my Trello lists. I spent multiple hours debugging my script because it just wasn't working when I finally realized where the problem was. I gave my python file the same name as the Trello package and therefore wasn't able to import the Trello python library into my project as the name was already taken. This must have been the dumbest bug I have ever had. After renaming my file everything worked just fine. With a few lines of code I was able to add all todo elements of my list into the Google Calendar without one event crossing with another.
![example Trello and Calendar](/images/TrelloListExample.png)
I am sorry for the bad image quality but as of writing this text it is already late into the night and I would normally already sleep at this point of time.
The planning of tasks obviously starts at the current time of the day. It wouldn't make sense to schedule an event at a time that has already passed.

So far my tasks all have a duration of 60 minutes and are scheduled one after another without restrictions. That needs to be fixed in the next step. The next step will include all the logic that is behind my system.

The first functionality I added were tasks that would be repeated every week. They would belong to the fixed task for which you can't change the time. An example would be the online conferences for school. I made a new Trello list for these tasks called "Weekly". Every time I run the script the due dates in Trello will automatically update to the next date from that time. By adding a | to the task title I am able to define how long the task is going to be. Example:  
*english conference | 120*  
The number is the time in minutes.

<!-- Todo -->