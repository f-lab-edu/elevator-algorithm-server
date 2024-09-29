import asyncio
import logging
from enum import IntEnum
from typing import Iterator, NamedTuple, Optional

from websockets.asyncio.server import serve

Step = int
Floor = int


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class RegisteredFloorRequest(NamedTuple):
    step: int
    current_floor: int
    target_floor: int


class ElevatorMomentumStatus(IntEnum):
    DOWN = 0
    UP = 1


class ElevatorStatus(IntEnum):
    DOWN = 0
    UP = 1
    STOP = 2


class Elevator():
    def __init__(
        self,
        id_: str,
        status=ElevatorStatus.STOP,
        floor=1,
    ):
        self.id = id_
        self.step = 1
        self.status: ElevatorStatus = status
        self.floor: int = floor
        self.max_floor: int = 10
        self.min_floor: int = 1
        self.watch_list: int = 0
        self.momentum: ElevatorMomentumStatus = ElevatorMomentumStatus.UP

    def get_symbol_from_status(self) -> str:
        return {
            ElevatorStatus.UP: "U",
            ElevatorStatus.DOWN: "D",
            ElevatorStatus.STOP: "E",
        }[self.status]

    def register_request(self, floor: int) -> None:
        self.watch_list |= 1 << (floor - 1)


    # def update_watch_list(self) -> None:
    #     process_watch_list = self.watch_list
    #     requested_floor = 1

    #     while process_watch_list:
    #         is_requested = bool(process_watch_list & 1)
    #         if not is_requested:
    #             process_watch_list >>= 1
    #             continue

    #         request_going_up = requested_floor > self.floor
    #         is_going_up = self.momentum == ElevatorMomentumStatus.UP
    #         is_matched_going_direction = request_going_up is is_going_up

    #         if is_matched_going_direction:
    #             self.watch_list |= 1 << (floor_request.current_floor - 1)
    #             self.watch_list |= 1 << (floor_request.target_floor - 1)


    def update_status(self) -> ElevatorStatus:
        current_floor_bitwise = 1 << (self.floor - 1)
        next_status = self.status
        if self.watch_list:
            condition_watch_list_bitwise = ((1 << self.floor) - 1) & self.watch_list
            print(f"{condition_watch_list_bitwise=:>10b}")
            if self.momentum == ElevatorStatus.DOWN:
                if condition_watch_list_bitwise > 0 and condition_watch_list_bitwise < current_floor_bitwise: next_status = ElevatorStatus.DOWN
                else: next_status = ElevatorStatus.UP
            else:
                if self.watch_list > current_floor_bitwise: next_status = ElevatorStatus.UP
                else: next_status = ElevatorStatus.DOWN
            self.momentum = next_status

            if self.watch_list & current_floor_bitwise > 0:
                next_status = ElevatorStatus.STOP

        self.watch_list -= (self.watch_list & current_floor_bitwise)
        if self.status != next_status:
            return ElevatorStatus.STOP if self.status != ElevatorStatus.STOP else next_status

        return self.status

    def update_floor(self) -> int:
        if self.status == ElevatorStatus.UP:
            return self.floor + 1
        if self.status == ElevatorStatus.DOWN:
            return self.floor - 1
        return self.floor

    def update(self) -> None:
        previous_status = self.status
        # self.update_watch_list()
        self.status = self.update_status()
        if self.status != ElevatorStatus.STOP: self.momentum = self.status
        if previous_status == self.status:
            self.floor = self.update_floor()
        self.step += 1

    def print_elavator(self, evalator_current_floor: int = 0) -> None:
        evalator_symbol = self.get_symbol_from_status()
        for floor in range(self.max_floor, self.min_floor-1, -1):
            evalator_current_symbol = evalator_symbol if floor == evalator_current_floor else ""
            print(f"{floor: >2}F | {evalator_current_symbol}")


class ElevatorManager():
    def __init__(self):
        self.elevators: dict[Elevator] = {}
    
    def add(self, elevator: Elevator) -> None:
        self.elevators[elevator.id] = elevator
    
    def get(self, name: str) -> Optional[Elevator]:
        return self.elevators.get(name)

    def update(self) -> Iterator[Elevator]:
        for elevator in self.elevators.values():
            if not elevator.watch_list: continue

            elevator.update()

            print(f"{elevator.step=}")
            print(f"{elevator.floor=}")
            print(f"{elevator.momentum=}")
            print(f"{elevator.watch_list=:>10b}")
            print(f"{elevator.status=}")
            print("===")
            elevator.print_elavator(elevator.floor)
            
            yield elevator


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
        elevator.register_request(int(floor))
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
