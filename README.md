# **Awaits** - makes working with asynchronous / multithreaded applications easier

> **Note:** All credit goes to the original creator [pomponchik](https://github.com/pomponchik), I've simply forked his [repo](https://github.com/pomponchik/awaits) and used google translate on the docs to help with my own understanding. 


This library solves 3 problems:

- Asynchronous programming using the async / await syntax loses its meaning if the code often contains pieces with "heavy" calculations or other tasks that block the event-loop. But now you can hang the decorator [```@awaitable```](#decorator-awaitable) on such a "heavy" function and it will become a coroutine that will be executed in a separate thread without blocking the event-loop. In all other respects, it will be a completely ordinary coroutine.
- Multi-threaded programming is verbose. To make your code run in multithreaded mode, you need to create thread objects, pass the desired functions there and start the threads. Now you just need to hang a decorator on an ordinary function and it will automatically be executed in multithreaded mode.
- Frequent creation of threads in a program requires constantly monitoring and management of the created threads. Here, a pool of threads becomes the minimum level of abstraction for you, not a separate thread. You can conveniently manage them within named groups called "rooms".

Read the documentation below to see how it all works.

## Table of Contents

- [**Quick start**](#quick-start)
- [**How does it work?**](#how-does-it-work)
- [**How does a thread group work?**](#how-does-a-thread-group-work?)
- [**What is a "room"?**](#what-is-a-"room"?)
- [**About the Task object**](#About-the-Task-object)
- [**Decorator ```@awaitable```**](#decorator-awaitable)
- [**Decorator ```@shoot```**](#decorator-shoot)
- [**Settings**](#settings)


## Quick start

Install awaits via [pip](https://pypi.org/project/awaits/):

```
$ pip install awaits
```

Now, just import the [```@awaitable```](#awaitable-decorator) and apply it to your function. No settings, nothing superfluous - everything is already working:

```python
import asyncio
from awaits.awaitable import awaitable


@awaitable
def sum(a, b):
  # Some complex dataset. Something that takes a long time to compute and prevents your event-loop from living.
  return a + b

# Now sum is a coroutine! While it is running in a separate thread, control is passed to the event-loop.
print(asyncio.run(sum (2, 2)))
```

Done! We made a non-blocking coroutine out of a regular function for your event-loop, to which we now apply the await syntax.

If your function returns nothing, another decorator can be applied to it, [```@shoot```](#decorator-shoot):

```python
from awaits.shoot import shoot


@shoot
def hello():
  # Also something heavy, but for some reason you don't need the result of which.
  print('Hello world!')

# The function will be "shot" executed in a separate thread without blocking the main one.
hello()
```

Your function will run on a different thread, while the main one might be doing something else.

Read more about the awaits library capabilities below.


## How does it work?

The base "shell" of this library is the [thread group](#how-does-a-thread-group-work?) (threads pool). The "heart" of the group is a queue with tasks (objects of class [```Task```](#about-task-object)). When you create a new group of threads, internally it spawns some threads with "workers" that are constantly waiting for new tasks from the queue. As soon as a new task appears in the queue, the first freed worker executes it.

To execute an arbitrary function in a group, you just need to pass it there along with the necessary arguments. In this case, the group will return you an object of the class [```Task```](#about-object-task), in which, by the value of the attribute ```done``` you can track whether your task has been completed or not. If it is done, you can pick up the result from the ```result``` attribute. For more information on working with thread groups, see [the appropriate section](#how-does-a-thread-group-work?).

For the convenience of managing multiple groups, the library contains the abstraction "room". At its core, it is a wrapper around a dictionary with groups of threads. By accessing the "room" by key, you either get a new group of threads if this group did not exist before, or an existing group if it was previously created. This eliminates the need to manually create thread groups.

The decorators use the "room" stored in the singleton. Wrapped in decorators [```@awaitable```](#decorator-awaitable) and [```@shoot```](#decorator-shoot) functions will be executed in groups of threads from the same room (by by default - in one thread group called ```base```).

Due to this arrangement, all thread management takes place "under the hood" and you no longer need to think about which thread your function will be executed in. It will be fulfilled in the one that is freed before anyone else.


## How does a thread group work?

A thread group is an instance of the ```ThreadsPool``` class. Let's import it:

```python
from awaits.pools.threads_pool import ThreadsPool
```

Threads will be created when the instance is initialized. You specify the number of threads in the group in the class constructor:

```python
threads = ThreadsPool(5)
```

Now that the group has been created, you can give it tasks using the ```do()``` method:

```python
def function(a, b, c, d=5, e=5):
  return a + b + c + d + e

task = threads.do(function, 1, 2, 3, d=10, e=20)
```

The first parameter is passed to the function to be executed, and then all the same parameters and in the same order as in the original call of this function.

What happened under the hood? The ```do()``` method created an object of class [```Task```](#about-task-object), passing there the function to be executed and all its parameters, and put it in the queue. He returned the task object to you so that you can track the progress and the result. Workers from other threads are constantly waiting for new items to appear in the queue. If at least one of them is free, he will immediately receive your task and complete it. If not, the task will wait in the queue for the first worker to be released.

Once the task is done, you can get the result:

```python
# The task.done flag set to True indicates that the task is complete and you can get the result.
while not task.done:
    pass

print(task.result)
```

If an error occurs during the execution of the function, the ```error``` attribute in the task object will be set to ```True```, and you can get an exception instance from the ```exception``` attribute:

```python
def error_function(a, b):
  return a / b

task = threads.do(error_function, 2, 0)

while not task.done:
    pass

if task.error:
  raise task.exception
```


## What is a "room"?

A room is an abstraction over thread groups, allowing assignments to be assigned to different groups by name. It is essentially a wrapper over a dictionary.

Let's create a room object:

```python
from awaits.threads_pools_room import ThreadsPoolsRoom


room = ThreadsPoolsRoom(5)
```

The number passed to the constructor is the number of threads in each of the groups in this room.

A specific thread group can be obtained using the dictionary syntax:

```python
pool = room['some_key']
```

Since this is the first time we are accessing the room with this key, it will create a new object of class [```ThreadsPool```](#how-thread-group-works) and return it. On subsequent calls with this key, it will return the same object.


## About the Task object

A task is an object of the [```Task```](#about-task-objects) class. The first argument to the object's constructor is the function to be executed, and the next - its arguments:

```python
from awaits.task import Task


def hello_something(something, sign='!'):
  hello_string = f'Hello {something} {sign}'
  print(hello_string)
  return hello_string

task = Task(hello_something, 'world')
```

In the non-activated state, the task simply stores the function and its arguments. To execute a function with the given arguments, you need to call the ```do()``` method on the task:

```python
task.do()
```

The ```task.done``` flag will be set to ```True``` when the task is completed. After that, you can get the execution result from the ```result``` attribute:

```python
while not task.done:
    pass

print(task.result)
```

If an error occurs during the execution of the function, the ```error``` attribute in the task object will be set to ```True```, and you can get an exception instance from the ```exception``` attribute:

```python
def error_function(a, b):
  return a / b

task = threads.do(error_function, 2, 0)

while not task.done:
    pass

if task.error:
  raise task.exception
```


## Decorator ```@awaitable```

After reading the documentation above, you have already learned how to create thread groups and rooms with them, as well as give threads to execute various tasks. However, it is not necessary to do even this manually.

The ```@awaitable``` decorator turns an ordinary function into a coroutine, that is, into a function that can be manipulated using Python's await syntax. Let's try to create a function like this:

```python
from awaits.awaitable import awaitable


@awaitable
def heavy_math_function(x, y):
  return x * y
```

When trying to execute a function, it will behave like a regular coroutine. However, in fact, its code will run on a thread group. While the code is running, control will be transferred to the event-loop.

```python
# Check that this is indeed a coroutine.
print (asyncio.run(heavy_math_function(5, 5)))
```

In this case, "under the hood", the task status is periodically polled, followed by "falling asleep" (by calling ```asyncio.sleep()```) for a certain period of time. Once the task is completed, its result is returned. If execution is interrupted by an exception, it is retrieved from [task object](#About-the-Task-object) and raised again.

The interval for which the function "sleeps" between readiness polls is taken by default from the [global settings](#settings) library. If necessary, you can specify it in the decorator factory (in seconds):

```python
@awaitable(delay = 0.5)
def heavy_math_function(x, y):
  return x * y
```

Manual control can be useful for you, for example, in the case of especially "heavy" functions that do not make sense to poll too often.

In addition, with a separate parameter, you can specify the name of the thread group in which you want the code to be executed. The default group is ```"base"```.

```python
@awaitable(pool='gravities')
def heavy_math_function(x, y):
  return x * y
```

## Decorator ```@shoot```

This decorator is simpler than [```@awaitable```](#awaitable-decorator). The function wrapped by it will simply be "shot" into the thread group, without waiting for the result. In this case, an object of the class [```Task```](#about-task-object) will be returned, which allows you to manually track the execution status.

```python
from awaits.shoot import shoot


@shoot
def other_heavy_math_function(x, y):
  return x * y

task = other_heavy_math_function(10, 10)

while not task.done:
    pass

print(task.result)
```

If necessary, you can specify the name of the thread group in which you want your function to be executed:

```python
@shoot(pool='gravities')
def other_heavy_math_function(x, y):
  return x * y
```

The default is also the ```"base"``` group.

> If the main flow of program execution comes to an end, the "shot" functions may not be executed in time, which may give you a false impression of a broken program. You should not use this decorator if it is critical for you.

## Settings

You can customize the default settings yourself. To do this, you need to call the ```set``` method of the ```config``` class:

```python
from awaits.config import config


# For example, set the polling rate of the task in the @awaitable decorator to 0.5 sec.
config.set(delay=10.5)
```

This method takes the following named parameters:

 **pool_size**(int) - number of threads in the group by default. It is important that this setting is set before completing the first task. If this parameter is not set, it will be equal to 10.

 **delay**(int or float) - delay value (in seconds) between iterations of polling task completion. Used by default in the [```@awaitable```](#awaitable-decorator). If you do not set this value manually, the number ```0.001``` will be used.