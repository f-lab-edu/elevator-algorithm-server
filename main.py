import asyncio
from websockets.asyncio.server import serve
from enum import IntEnum
from typing import NamedTuple

Step = int
Floor = int


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
        status=ElevatorStatus.STOP,
        floor=1,
    ):
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

async def consumer_handler(ws, elevator: Elevator) -> None:
    while True:
        message = await ws.recv()
        name, type_, floor = message.split(":")

        print(name, type_, floor)
        elevator.register_request(int(floor))

async def producer_handler(ws: str, elevator: Elevator) -> None:    
    # TODO: change to asyncio generator
    while True:
        while elevator.watch_list:
            elevator.update()
            id_ = "ELEVATOR0"
            print(f"{elevator.step=}")
            print(f"{elevator.floor=}")
            print(f"{elevator.momentum=}")
            print(f"{elevator.watch_list=:>10b}")
            print(f"{elevator.status=}")
            print("===")
            elevator.print_elavator(elevator.floor)

            await ws.send("STEP:" + id_ + ":" + str(elevator.step))
            await ws.send("FLOOR:" + id_ + ":" + str(elevator.floor))
            await ws.send("MOMENTUM:" + id_ + ":" + str(elevator.momentum))
            await ws.send("WATCH_LIST:" + id_ + ":" + str(elevator.watch_list))
            await ws.send("STATUS:" + id_ + ":" + str(elevator.status))

            await asyncio.sleep(1)
        await asyncio.sleep(0.1)



async def handler(ws: str) -> None:
    elevator = Elevator()
    consumer_task = asyncio.ensure_future(consumer_handler(ws, elevator))
    producer_task = asyncio.ensure_future(producer_handler(ws, elevator))

    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()


async def main() -> None:
    async with serve(handler, "127.0.0.1", 5678):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
