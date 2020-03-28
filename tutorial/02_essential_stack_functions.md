# Essential stack functions

## `dup`

`(1 2 3 .dup) <=> (1 2 3 3)`

## `drop`

`(1 2 3 .drop) <=> (1 2)`

## `swap`

`(1 2 3 .swap) <=> (1 3 2)`

## `rot`

`(1 2 3 4 .swap) <=> (1 4 3 2)`

## `over`

`(1 2 3 .over) <=> (1 2 3 2)`

## `over`

`(1 2 3 .over) <=> (1 2 3 2)`

## `help`

If you ever forget what a certain function does, you can get help on it:
```
[stekk v0.0.1] over
built-in function over (a, b)
[stekk v0.0.1] (over .help)
a b -- a b a
```

# Examples

You can try these problems on your own first!

Important requirement: if you need to calculate something, you might need
to "clean up" after your computations. For instance, if you're writing a
function that takes 3 arguments `a`, `b` and `c` and returns two values
`r` and `q`, then the only things the function should remove from the stack
(in the end) are `a`, `b` and `c`; the only things the function should then add
are `r` and `q`. 

Obviously, your solution may be different from the one in the spoiler.

## 1.

Given two numbers `a` and `b` on top of the stack, calculate `a*a + b*b`.

<details>
    <summary>Solution</summary>

`a*a+b*b := {(.dup .* .swap .dup .* .+)};`

*(Yep, that's a valid variable name!)*

What happens here?

```
    : (a b) 
dup : (a b b)
*   : (a [b^2])
swap: ([b^2] a)
dup : ([b^2] a a)
*   : ([b^2] [a^2])
+   : ([b^2 + a^2]) -- which is the desired result
```

</details>

## 2.

Given two integers, `a` and `b`, return `a % b`, remainder of dividing
`a` by `b`.

Hint: `/i` is the integer division function (`/f` is floating-point division,
but it isn't useful here)

<details>
    <summary>Solution</summary>

Let's denote integer division as `//`. The first integer less than or equal to
`a` that is divisible by `b` is `b * (a // b)`. Then the remainder will just
be the difference between `a` and that number.

So the formula is `a % b = a - b*(a // b)`.

Solution:
```
a%b := {(.over .over ./i .* .-)};
```

</details>

### 2.1. 

And now you have to check whether `b` is zero. In that case, return `$E`.

<details>
    <summary>Solution</summary>

    a%b := {
        if (.dup 0 .=)
            $E
        else
            (.over .over ./i .* .-)
    };

</details>


## 3.
Given `N`, return the sum of all natural numbers from `1` to `N`. Don't use
the formula -- actually add the numbers up recursively.

<details>
    <summary>Solution</summary>

```
__nat_sum := {
    ;; given: acc n

    if (.dup 0 .<=)
        (.drop)         ;; return acc
    else
        (.dup .rot      ;; n n acc
         .+             ;; n [n+acc]
         .swap          ;; [n+acc] n
         1 .-           ;; [n+acc][n-1]
         .__nat_sum)
};

nat_sum := {
    (0 .swap .__nat_sum)
};
```

</details>

