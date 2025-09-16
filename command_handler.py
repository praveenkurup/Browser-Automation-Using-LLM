from queue import Queue
import time


class handleCommands:
    def __init__(self, task_queue: Queue):
        self.task_queue = task_queue
        self.exit = False

    def process_command(self, command):
        if command == "help":
            response = """HELP:-
                - help :- Shows all the command options
                - exit :- To exit the program"""
            print(response)
            return
        elif command == "exit":
            self.task_queue.put("exit")
            self.exit = True
            return
        else:
            self.task_queue.put(command)

    def start_command_loop(self):
        while not self.exit:
            command = input("> ")
            self.process_command(command)
            continue