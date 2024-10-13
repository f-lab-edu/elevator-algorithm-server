import asyncio
import logging
from enum import IntEnum
from typing import Iterator, NamedTuple, Optional

from websockets.asyncio.server import serve

from elevator import Elevator


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class ElevatorManager():
    def __init__(self):
        self.elevators: dict[Elevator] = {}
    
    def add(self, elevator: Elevator) -> None:
        self.elevators[elevator.name] = elevator
    
    def get(self, name: str) -> Optional[Elevator]:
        return self.elevators.get(name)

    def update(self) -> Iterator[Elevator]:
        for elevator in self.elevators.values():
            if not elevator.watch_list: continue

            elevator.update()
            self.print_elevator_status(elevator)
            
            yield elevator

    def print_elevator_status(self, elevator):
        print(f"{elevator.step=}")
        print(f"{elevator.floor=}")
        print(f"{elevator.momentum=}")
        print(f"{elevator.watch_list=:>10b}")
        print(f"{elevator.status=}")
        print("===")
        elevator.print_elavator(elevator.floor)


class TransportManager():
    def __init__(self, ws):
        self.ws = ws
        self.logger = logger
        self.logger.info("SESSION ESTABLISHED!")

    def _process_request(self, message: str) -> tuple[str, str, str]:
        name, type_, floor = message.split(":")
        return name, type_, floor

    async def recv(self) -> tuple[str, str, str]:
        message = await self.ws.recv()
        self.logger.info("RECV: " + message)
        return self._process_request(message=message)
    
    async def send(self, message: str) -> None:
        self.logger.info("SEND: " + message)
        await self.ws.send(message)


async def consumer_handler(transport_manager: TransportManager, elevator_manager: ElevatorManager) -> None:
    async for message in transport_manager.ws:
        name, type_, floor = message.split(":") #await transport_manager.recv()
        elevator = elevator_manager.get(name)
        elevator.register_request(int(floor), type_)
    transport_manager.logger.info("SESSION ENDS")


async def producer_handler(transport_manager: TransportManager, elevator_manager: ElevatorManager) -> None:
    # TODO: change to asyncio generator
    while True:
        is_idle = True
        for elevator in elevator_manager.update():
            is_idle = False
            await transport_manager.send("STEP:" + elevator.id + ":" + str(elevator.step))
            await transport_manager.send("FLOOR:" + elevator.id + ":" + str(elevator.floor))
            await transport_manager.send("MOMENTUM:" + elevator.id + ":" + str(elevator.momentum))
            await transport_manager.send("WATCH_LIST:" + elevator.id + ":" + str(elevator.watch_list))
            await transport_manager.send("STATUS:" + elevator.id + ":" + str(elevator.status))
        if not is_idle: await asyncio.sleep(1)
        await asyncio.sleep(0.1)


async def handler(ws: str) -> None:
    elevator_manager = ElevatorManager()
    elevator_manager.add(Elevator("ELEVATOR1"))
    elevator_manager.add(Elevator("ELEVATOR2"))
    transport_manager = TransportManager(ws=ws)

    consumer_task = asyncio.ensure_future(consumer_handler(transport_manager, elevator_manager))
    producer_task = asyncio.ensure_future(producer_handler(transport_manager, elevator_manager))

    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()

    print(pending)
    print("SESSION CLEAR!")


async def main() -> None:
    async with serve(handler, "0.0.0.0", 5678):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
