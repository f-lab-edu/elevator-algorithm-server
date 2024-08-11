import os
from enum import IntEnum
from time import sleep
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
        registered_floor_requests=[],
    ):
        self.step = 1
        self.status: ElevatorStatus = status
        self.floor: int = floor
        self.registered_floor_requests: list[RegisteredFloorRequest] = registered_floor_requests
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

    def update_watch_list(self) -> None:
        nq = []
        for floor_request in self.registered_floor_requests:
            request_going_up = floor_request.target_floor - floor_request.current_floor > 0
            is_going_up = self.momentum == ElevatorMomentumStatus.UP
            is_matched_going_direction = request_going_up is is_going_up

            if (not is_matched_going_direction or self.step < floor_request.step) and self.watch_list:
                nq.append(floor_request)
                continue

            self.watch_list |= 1 << (floor_request.current_floor - 1)
            self.watch_list |= 1 << (floor_request.target_floor - 1)
                
        self.registered_floor_requests = nq

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
        self.update_watch_list()
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


def parse_input() -> list[RegisteredFloorRequest]:
    registered_floor_requests: list[RegisteredFloorRequest] = []
    with open("./input.txt", "r", encoding="utf8") as f:
        lines = f.readlines()
        for line in lines:
            step, current_floor, target_floor = line.split(" ")
            registered_floor_requests.append(RegisteredFloorRequest(int(step), int(current_floor), int(target_floor)))
    return registered_floor_requests


def main() -> None:
    elevator = Elevator(registered_floor_requests=parse_input())
    while elevator.watch_list or elevator.registered_floor_requests:
        # os.system("clear")
        elevator.update()
        print(f"{elevator.step=}")
        print(f"{elevator.floor=}")
        print(f"{elevator.momentum=}")
        print(f"{elevator.watch_list=:>10b}")
        print(f"{elevator.status=}")
        print(f"{elevator.registered_floor_requests=}")
        print("===")
        elevator.print_elavator(elevator.floor)
        sleep(0.3)


if __name__ == "__main__":
    main()

# 필요한 스킬
# Communication => Clarification (문제 정의를 명확화 하는 과정 부족)
# 설계 (타이핑 + 구조 + 흐름)
# 알고리즘 (비트 연산, 최적화)
# 안전한 코드 짜는 방법
# 디버그

# 다음에 할 것
# 인원수를 반영하기 (엘레베이터에 더이상 태울사람이 없으면 skip | 정원 10명)
# 2대 엘레베이터 가정, skip 조건
