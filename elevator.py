import math
from typing import NamedTuple
from enum import IntEnum

Step = int
Floor = int


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
        name: str,
        status=ElevatorStatus.STOP,
        floor=1,
    ):
        self.name = name
        self.step: int = 1
        self.floor: int = floor
        self.max_floor: int = 10
        self.min_floor: int = 1
        self.down_watch_list: int = 0
        self.up_watch_list: int = 0
        self.status: ElevatorStatus = status
        self.momentum: ElevatorMomentumStatus = ElevatorMomentumStatus.UP

    def get_status_from_symbol(self, symbol: str) -> ElevatorStatus:
        return {
            "U": ElevatorStatus.UP,
            "D": ElevatorStatus.DOWN,
            "E": ElevatorStatus.STOP
        }[symbol]

    def get_symbol_from_status(self) -> str:
        return {
            ElevatorStatus.UP: "U",
            ElevatorStatus.DOWN: "D",
            ElevatorStatus.STOP: "E",
        }[self.status]

    def register_request(self, floor: int, button_type: str) -> None:
        if button_type == 'UP':
            self.up_watch_list |= 1 << (floor - 1)
        elif button_type == 'DOWN':
            self.down_watch_list |= 1 << (floor - 1)

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

    # def update_status(self) -> ElevatorStatus:
    #     current_floor_bitwise = 1 << (self.floor - 1)
    #     next_status = self.status
    #     if self.watch_list:
    #         condition_watch_list_bitwise = ((1 << self.floor) - 1) & self.watch_list
    #         print(f"{condition_watch_list_bitwise=:>10b}")
    #         if self.momentum == ElevatorStatus.DOWN: # 내려가는중
    #             if ( condition_watch_list_bitwise > 0 # 지금보다 아래층에 갈곳이 있을 때
    #                  and condition_watch_list_bitwise < current_floor_bitwise): # 현재층에 안멈출때
    #                 next_status = ElevatorStatus.DOWN
    #             else: next_status = ElevatorStatus.UP
    #         else:
    #             if self.watch_list > current_floor_bitwise: next_status = ElevatorStatus.UP
    #             else: next_status = ElevatorStatus.DOWN
    #         self.momentum = next_status

    #         if self.watch_list & current_floor_bitwise > 0: # 내려야함
    #             next_status = ElevatorStatus.STOP

    #     self.watch_list -= (self.watch_list & current_floor_bitwise)
    #     if self.status != next_status:
    #         return ElevatorStatus.STOP if self.status != ElevatorStatus.STOP else next_status

    #     return self.status

    def update_status(self) -> ElevatorStatus:
        current_floor_bitwise = 1 << (self.floor - 1)
        if self.status == ElevatorStatus.STOP:
            return self._handle_stop(current_floor_bitwise)

        if self.status == ElevatorStatus.DOWN: # 내려가는 중
            return self._handle_moving_down(current_floor_bitwise)

        if self.status == ElevatorStatus.UP:
            return self._handle_moving_up(current_floor_bitwise)


    def _handle_stop(self, current_floor_bitwise: int) -> ElevatorStatus:
        # 엘레베이터의 momentum이 UP이었던 경우 현재 층보다 위에서 요청이 있는 경우에 올라간다
        if self.momentum == ElevatorMomentumStatus.UP:
            up_bitwise = (1 << self.max_floor) - (current_floor_bitwise << 1)
            if (self.up_watch_list | self.down_watch_list) & up_bitwise:
                return ElevatorStatus.UP

        # 엘레베이터의 momentum이 Down인 경우 현재 층보다 아래 층에 요청이 있는 경우 내려간다
        elif self.momentum == ElevatorMomentumStatus.DOWN:
            down_bitwise = current_floor_bitwise - 1
            if (self.up_watch_list | self.down_watch_list) & down_bitwise:
                return ElevatorStatus.DOWN
        
        # 이외의 경우는 현재 중지 상태인 것이다.
        # up요청과 down 요청 중 가장 큰 요청부터 처리한다
        return self._handle_idle(current_floor_bitwise)


    def _handle_moving_up(self, current_floor_bitwise: int) -> ElevatorStatus:
        # 올라갈때 up_request가 있으면 태우고 올라감
        need_to_stop = current_floor_bitwise & self.up_watch_list
        if need_to_stop:
            self.up_watch_list -= (need_to_stop) # TODO - naming
            return ElevatorStatus.STOP
        
        # 올라갈때 down_request는 가장 높은 down_request만 고려함
        if self.down_watch_list == 0:
            return ElevatorStatus.STOP
        
        # TODO - 로직이 틀림. 
        top_of_down_request = 1 << (self.down_watch_list.bit_length() - 1)
        need_to_stop = top_of_down_request & current_floor_bitwise
        if need_to_stop:
            self.down_watch_list -= (need_to_stop)
            return ElevatorStatus.STOP
        
        return ElevatorStatus.UP

    def _handle_moving_down(self, current_floor_bitwise) -> ElevatorStatus:
        # 내려갈 때 down request에 현재층이 있으면 태우고 내려감
        # 내려갈 때 up_request는 무시함(예외 1층)
        need_to_stop = current_floor_bitwise & self.down_watch_list
        if need_to_stop:
            self.down_watch_list -= (need_to_stop)
            return ElevatorStatus.STOP
        
        need_to_stop = (current_floor_bitwise == self.up_watch_list == 1)
        if need_to_stop:
            self.up_watch_list -= need_to_stop
            return ElevatorStatus.STOP
        
        return ElevatorStatus.DOWN

    def _handle_idle(self, current_floor_bitwise):
        if self.up_watch_list == 0 and self.down_watch_list == 0:
            return ElevatorStatus.STOP
        
        up_max = down_max = 1
        up_min = down_min = self.max_floor

        if self.up_watch_list != 0:
            up_min = int(math.log2(self.up_watch_list & -self.up_watch_list) + 1)
            up_max = 1 << (self.up_watch_list.bit_length() - 1)

        if self.down_watch_list != 0:
            down_min = int(math.log2(self.down_watch_list & -self.down_watch_list) + 1)
            down_max = 1 << (self.down_watch_list.bit_length() - 1)

        to_max = max(up_max, down_max)
        to_min = min(up_min, down_min)

        if to_max == to_min:
            if current_floor_bitwise > to_max:
                direction = 'D'
            elif current_floor_bitwise == to_max:
                direction = 'E'
            else:
                direction = 'U'
            
            return self.get_status_from_symbol(direction)

        if current_floor_bitwise > to_max:
            direction = 'D'
        elif to_max >= current_floor_bitwise > to_min:
            to_max_dist = int(math.log2(to_max // current_floor_bitwise))
            to_min_dist = int(math.log2(current_floor_bitwise // to_min))
            direction = 'U' if to_max_dist > to_min_dist else 'D'
        elif to_min >= current_floor_bitwise:
            direction = 'U' if to_min > current_floor_bitwise else 'E'

        return self.get_status_from_symbol(direction)


    def update_floor(self) -> int:
        if self.status == ElevatorStatus.UP:
            return min(self.floor + 1, self.max_floor)
        if self.status == ElevatorStatus.DOWN:
            return max(self.floor - 1, self.min_floor)
        return self.floor

    def update_momentum(self) -> ElevatorMomentumStatus:
        if self.status != ElevatorStatus.STOP:
            return ElevatorMomentumStatus(self.status)
        
        return self.momentum

    def update(self) -> None:
        previous_status = self.status
        # self.update_watch_list()
        self.status = self.update_status()
        self.momentum = self.update_momentum()
        self.floor = self.update_floor()
        self.step += 1

    def print_elavator(self, evalator_current_floor: int = 0) -> None:
        evalator_symbol = self.get_symbol_from_status()
        for floor in range(self.max_floor, self.min_floor-1, -1):
            evalator_current_symbol = evalator_symbol if floor == evalator_current_floor else ""
            print(f"{floor: >2}F | {evalator_current_symbol}")


    def __repr__(self) -> str:
        return (
            f'Elevator('
            f'floor={self.floor}, '
            f'status={self.status}, '
            f'momentum={self.momentum}, '
            f'down_watch_list={self.down_watch_list}, '
            f'up_watch_list={self.up_watch_list})'
        )

if __name__ == "__main__":
    with open('input.txt') as f:
        commands = f.readlines()
    print(commands)
    elev = Elevator('ELEVATOR1')
    for command in commands:
        name, button_type, floor = command.split()
        elev.register_request(int(floor), button_type)
    print(elev)
    for _ in range(20):
        elev.update()
        print(elev)
    # while elev.down_watch_list | elev.up_watch_list:
    #     elev.update()
    #     elev.print_elavator(elev.floor)
    #     print('=====================')
