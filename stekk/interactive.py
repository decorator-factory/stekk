# this module is just a spaghetti contraption
# touch carefully

import re
import lark
import stekk
import click

import os
here, _ = os.path.split(__file__)

function_t = type(lambda: ...)

UP_ARROW = "\x1b[A"
DOWN_ARROW = "\x1b[B"

with open(os.path.join(here, "interactive/ascii_art"), "r") as file:
    ascii_art = file.read()

pre_string = f"[stekk v{stekk.version}]"

def is_name_char(char):
    return bool(re.match(r"[a-zA-Z0-9<>+\-*\/~\^&|%?_'=!]", char))

def backspace(width):
    click.echo("\b"*width, nl=False)
    click.echo(" "*width, nl=False)                     
    click.echo("\b"*width, nl=False)


def console(vm=None):
    if vm is None:
        click.secho(ascii_art, fg='bright_green')
        vm = stekk.vm.VM([])

    history = []
    total_command = ""

    while True:
        if total_command == "":
            click.secho(pre_string + " ", nl=False, fg='cyan')
        else:
            click.echo("..." + " "*(len(pre_string) - 2), nl=False)
    
        try:
            command = ""
            remembered = ""

            history_index = 0
            click.echo(command, nl=False)
            c = click.getchar()

            while c not in '\n\r':
                if len(c) != 1:
                    if c == UP_ARROW and len(history) > history_index:
                        if history_index == 0:
                            remembered = command

                        backspace(len(command))

                        command = history[-history_index-1]
                        history_index += 1
                        click.echo(command, nl=False)

                    elif c == DOWN_ARROW:
                        if history_index == 0:
                            backspace(len(command))
                            command = remembered
                        else:
                            history_index -= 1
                            backspace(len(command))
                            command = history[-history_index-1]
                            click.echo(command, nl=False)

                elif c == "\t":
                    i = 0
                    while len(command)>i and is_name_char(command[-i-1]):
                        i += 1

                    indent = False

                    if i == 0:
                        indent = True
                    else:
                        while i > 0:
                            subs = command[-i:]
                            possible = [name for name in vm.names
                                        if name.startswith(subs)]
                            if possible:
                                break
                            i -= 1
                        if i == 0:
                            indent = True
                        else:
                            if command[-i-1:-i] == ".":
                                possible = [name for name in possible
                                            if isinstance(
                                                vm.names[name],
                                                (
                                                    function_t,
                                                    stekk.parser.CodeBlock,
                                                    stekk.util.StrWrapper
                                                ))]
                            while len(possible) > 1:
                                ps = " " + " ".join(possible)
                                click.secho(ps, nl=False, fg="bright_green")
                                c = click.getchar()
                                if c.isdigit() and 0 <= int(c)-1 < len(possible):
                                    possible = [possible[int(c)-1]]
                                    c = ""
                                else:
                                    possible = [name for name in possible
                                                if name.startswith(subs + c)]
                                    if c == " " or c.isprintable():
                                        subs += c
                                        command += c
                                        i += 1
                                    else:
                                        c = ""

                                backspace(len(ps))
                                click.echo(c, nl=False)

                            if len(possible) == 1:
                                completion = possible[0][i:]
                                command += completion
                                click.echo(completion, nl=False)

                    if indent:
                        command += "    "
                        click.echo("    ", nl=False)
                elif ord(c) == 127: # backspace
                    if command != "":
                        backspace(1)
                        command = command[:-1]
                else:
                    click.echo(c, nl=False)
                    command += c
                c = click.getchar()

            if (history == [] or history[-1] != command) and command != "":
                history.append(command)

            click.echo("")
        except KeyboardInterrupt:
            click.echo("")
            total_command = ""
            command = ""
        except EOFError:
            click.echo("")
            return


        if command.endswith("\\"):
            total_command += command[:-1] + "\n"
            continue
        else:
            total_command += command + "\n"

        command_to_run = total_command
        total_command = ""

        try:
            statements = stekk.parser.parse(command_to_run)
        except stekk.parser.StekkSyntaxError as e:
            click.secho(str(e.error), fg='bright_red')
        except lark.exceptions.ParseError: # end of input
            total_command = command_to_run
        else:
            try:
                vm.execute_statements(statements)
                if vm.last_result is not None:
                    click.echo(vm.last_result) 
                vm.last_result = None
            except KeyboardInterrupt as e:
                continue
            except Exception as e:
                click.secho(f"{e.__class__.__name__}: {e.args}", fg='bright_red')
