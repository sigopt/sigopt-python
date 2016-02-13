# SigOpt API Examples
For the complete API documentation, visit [https://sigopt.com/docs](https://sigopt.com/docs).
## Python
Check out our basic python example and implement your own function to evaluate. Dive deeper with our parallel example, which runs multiple optimization loops at the same time.
## Other Languages
If you've got an executable file written in another language, you can use the example we've written where the `evaluate_metric` function run an executable file in a sub process. 

This script will pass the suggested assignments as command line arguments, and will expect the script's output to be a float representing a fuction evaluated on these assignments. 

To start, you'll need to create an experiment with parameter names matching the command line arguments of your program. 

For example, if your filename is test and you have one double parameter with suggested value 11.05, this script will run
```
./test --x=11.05
```
Feel free to use, or modify for your own needs!



