# Example of how to queue an user task.
# Endpoints of the worker API can be seen at http://localhost:8000/docs.

import requests


def main() -> None:
    url = "http://localhost:8000/task_queue" #cambiar localhost por la ip del servidor donde se encuentre el worker
    data = {
        "task_name": "tasks.misc.test_sum",
        "args": [5, 10],
    }
    
    response = requests.post(url, json=data)

    print(response.json())


if __name__ == "__main__":
    main()
