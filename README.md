I am amazed to see how much Claude Code and Google Gemini could do carrying out all kind of tasks, with me writing one single line of python code.

In Claude Code and google Gemini, I could write instructions using regular words and sentences and python codes would be created to carry out all kinds of tasks.  There are 2 features I particularly like:

1)  Both Claude Code and Google Gemini could be working on Macbook terminal. No python IDEs are needed. Most of my codes are developped in Linux interface or jupyter notebook.  Claude Code works without the need of IDE. So it fits me really well.
2)  Claude Code or Google Gemini could test the python codes it created and if it find some errors, it will try to correct itself.  I really like this self-validation and self improving capacity.
3)  If the results are not satisfcatory, I could always ask Claude Code to try harder and most of the time, I could get what I need.

This Git repository is to keep some fun exercises I worked on recently. In each sample projects, there are will instructions, such as instruction1.txt, instruction2.txt.  
Then the instructions are in a sample project, then the typ[ical command are like this:  " Please carry out the task as specified in instruction1.txt"

Assuming that you have set up the Claude in your Macbook and set up the credentials for Claude or OpenAI in .env, here is what I usually do:

1) In your work directory (in my case it is: /Users/max-imac/MaxWork/gemini_cli), Create a project directory for example : webcrawler_universitysearch. Set your workdir=webcrawler_universitysearch,
2) cd $workdir
3) input at the terminal "claude" or "geminiu"
4) Then writeyour first instruction in the file  "instruction1.txt"
5) Input the command at Claude console such as "Please carry out the task as specified in instruction1.txt"
6) Then Following the claude console to give follow-up instruction.

Here is one example of instruction1.txt for my project1, which is to download all MS and PhD strudents from the Stats Dept of Purdue Universities:

Could you write python code to extract all students from this website: https://www.stat.purdue.edu/people/graduate_students/index.html?  I would you to extract all 
  the following information: 
	1) Student Name
	2) Program (MS or PhD),  
        3) Office location 
        4) Email.  
If some information is missing, then leave if blank.  I would like the output to a csv file with file name: students.csv

Please reach out to me if you have any questions about how to use the Claudec Code to carry out simple tasks.  Here is the instruction for setting up the Claude in your Macbook:
https://docs.anthropic.com/en/docs/claude-code/setup

The cost of set upo Claude Code to do all these are $20 / month.  I used OpenAI to LLm -related-task.  It may cost a few dollars as well.

   
