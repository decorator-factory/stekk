# Basics

Welcome to `stekk`! This language will put great strain on your brain.
Prepare to think creatively in order to solve simple problems like sorting,
searching and text processing. `stekk` is a stack-based language, just like
Forth, so you'll have to write your programs almost 'in reverse order'. You
will like the autocompletion, though!

# The interactive console

Run the interactive console with `python3 -m stekk` in the directory where
`examples`, `stekk`, `tutorial` and `README.me` are located.

The interactive console allows you to execute little pieces of a program.
If you type something into the console and press ENTER, you will see the result
of what you typed.

```
[stekk v0.0.1] "Hello, world!"
Hello, world!
[stekk v0.0.1] 1234
1234
[stekk v0.0.1] 0.00000000005
5e-11
```

# Variables 
 
A `variable` is a means of naming things. A variable is a name that refers
to some place in the RAM where the object is stored.

You can store all kinds of things in variables: numbers, tuples, lists,
strings, 

Examples:

```
[stekk v0.0.1] salary := 1200            
[stekk v0.0.1] salary
1200
```

Here are some examples of variable names:
```
finished?   old>new   teeny-weeny
y''         old&new   tax%
help_Me!!   old=new   |dist|   
```
As you can see, you can put special characters in variable names.
It allows for good conventions: for instance, use `available?` instead of
`is_available`; for functions that change some state, put an `!` at the end:
`ban!`.
On the other hand, it allows for crazy and obscure names:
```
?&%?!<=!?==>:="Hello, world!"
```

# The stack

Every program in `stekk` works with a stack. Imagine a real-word stack of 
cards or plates with things written on them. You can only push something on
top of the stack or take something from its top. In other words, a stack is an
array that only supports two operations:
1. Pop the topmost element
2. Push a new element on top

Take a look at this:
```  
[stekk v0.0.1] (1 2 3)    
3
[stekk v0.0.1] ()
2
[stekk v0.0.1] ()
1
[stekk v0.0.1] ()
[stekk v0.0.1] 
```

Let me explain what happens here.

`(1 2 3)` is an expression. It will execute the following instructions:
1. push 1 on top of the stack
2. push 2 on top of the stack
3. push 3 on top of the stack

After all this was executed, the topmost element is popped from the stack to
become the value of a stack expression. So you can do this:

```
[stekk v0.0.1] x := (1 2 3)
[stekk v0.0.1] x
3
```

`()` is an empty stack expression. It just pops an element from the stack.

You can use it to emulate Python's 'multiple assignment':

```
[stekk v0.0.1] a := (1 2 3)
[stekk v0.0.1] b := ()
[stekk v0.0.1] c := ()
[stekk v0.0.1] [a, b, c]
[3, 2, 1]
```


# How to see the stack?

`.__stack` returns the stack as a `list`. I'll explain the syntax later.
```
[stekk v0.0.1] (1 2 3 4 5 0)
0
[stekk v0.0.1] (.__stack)
[1, 2, 3, 4, 5]
```


# Function calls

`.function` denotes a function call. A function operates on the stack as well.

```
[stekk v0.0.1] (3 7 .+)
10
```

In this example, this happens:
1. 3 is pushed onto the stack
2. 7 is pushed onto the stack
3. A function called `+` is called. This function takes two topmost elements
from the stack and pushed their sum onto the stack.

Another example:
```
[stekk v0.0.1] one := 1
[stekk v0.0.1] two := 2
[stekk v0.0.1] three := (one two .+)
[stekk v0.0.1] three
3
```


# Code blocks

In stekk, you can treat a piece of code just like you treat any other value.
To store a piece of code, use a *code block*.

Reopen the interactive console (I will explain why later);
```
[stekk v0.0.1] greet := {
...                ("Hello, world!" .println) 
...            }
[stekk v0.0.1] greet
{Stack('Hello, world!' fcall(Name[println]))}
```
There isn't really any difference between a function and a code block.
You can execute the code block like this:
```
[stekk v0.0.1] .greet
Hello, world!
```

What happens when you execute one of these lines?

```
x := .greet

x := (.greet)
```

In both cases, a special *constant* `$N` will get assigned to x:
```
[stekk v0.0.1] x := .greet
Hello, world!
[stekk v0.0.1] y := .greet
Hello, world!
[stekk v0.0.1] x  
$N
[stekk v0.0.1] y
$N
```

`$N` is a constant that means `null`, `nothing`, `not found` and so on.

However, a function can return a value. This value is simply the result of the
last expression. In this case, `("Hello, world!" .println)` didn't have any
value because at the `)` character the stack was empty. This isn't very useful:
if something useful was on top of the stack, it would be popped and likely
discarded! 

```
[stekk v0.0.1] (1 2 3)
3
[stekk v0.0.1] .greet
Hello, world!
2
```

Let's modify our function so that it returns `42` and doesn't mess with the stack.

```
[stekk v0.0.1] greet := {
...                ("Hello, world!" .println 42)
...            }
[stekk v0.0.1] .greet
Hello, world!
42
```

# Running code from a file

Inside a program or a code block, all statements must end with a `;`, except for
the last one:

```
a := 1;    or    a := 1;
b := 2           b := 2;
```

To run a file with your program, do this:
```
python3 -m stekk <path_to_file>
```

Try running some examples:
```
python3 -m examples/fibonacci.stekk
```
