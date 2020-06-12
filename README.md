
# ITC 2019: International Timetabling Competition

## Quick Start

On Linux, do
```bash
git clone git@github.com:Jachtabahn/timetabling.git
cd timetabling
python parse.py -vv
```

The [timetabling problem](https://www.itc2019.org/home) consists in finding a good assignment of courses to time slots during a University semester and an assignment of students and lecturers to those courses. It is a very complex combinatorial optimization problem.

I've only begun thinking about this and wrote a very simple script to parse the instances and compute a simple assignment. The above code launches this script to output a simple assignment.
