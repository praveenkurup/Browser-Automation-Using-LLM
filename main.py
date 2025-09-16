import command_handler
import llm_handler
from multiprocessing import Process, Queue


def main():
    print("Browser automation using LLM - Made by github.com/praveenkurup")

    task_queue = Queue()

    llm = Process(target=llm_handler.main, args=(task_queue,))
    llm.start()

    command_handler_instance = command_handler.handleCommands(task_queue)

    command_handler_instance.start_command_loop()

    llm.join()

if "__main__" == __name__:
    main()