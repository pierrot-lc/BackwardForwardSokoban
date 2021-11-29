"""Gym environments for the sokoban.
"""
import numpy as np

from gym_sokoban.envs import sokoban_env

from utils import print_board, build_board_from_raw
from variables import TYPE_LOOKUP
from macro_move import macro_moves


class MacroSokobanEnv(sokoban_env.SokobanEnv):
    """Casual Sokoban with macro-moves.

    The environment is the same, but now a step
    in the environment is a macro-move.
    A macro-move is a serie of moves where
    only one box is pushed or pulled.

    The reward is also changed. We only give a reward of +1
    when the agent won the game.

    This environment can manage a forward or a backward sokoban.
    """
    def __init__(
        self,
        forward: bool,
        dim_room: tuple[int]=(10, 10),
        max_steps: int=120,
        num_boxes: int=4,
        num_gen_steps: int=None,
        ):
        self.forward = forward

        # List of all reachable states, saving for computation efficiency
        self.states = None  # Default value, the computation has to be done once

        super().__init__(dim_room, max_steps, num_boxes, num_gen_steps)

    def render(self, mode='raw'):
        """Render in 'raw' mode by default.
        """
        return super().render(mode=mode)

    def print(self):
        """Print the current environment.
        """
        raw = self.render()
        board, player = build_board_from_raw(raw)
        print_board(board, player)

    def reset(self, render_mode: str='raw', second_player=None) -> np.array:
        """Same reset method as the super class, except when in backward mode.
        In backward mode, we do the same reset method,
        but the initialization is changed: all boxes are placed on the targets.
        """
        raw = super().reset(render_mode=render_mode)
        if self.forward:
            return raw

        # Backward mode
        # Place every boxes on target
        self.room_state[self.room_state == TYPE_LOOKUP['box target']] = TYPE_LOOKUP['box on target']
        self.room_state[self.room_state == TYPE_LOOKUP['box not on target']] = TYPE_LOOKUP['empty space']

        self.boxes_on_target = self.num_boxes

        return self.render(render_mode)

    def step(self, room_state: np.array):
        """Update the environment state.

        Args
        ----
        :room_state: The new state of the environment.
            This state has to be one of the states generated
            by the `self.moves()` method, to ensure this is a state
            generated by a macro-move.
        """
        # Apply movement
        self.num_env_steps += 1
        self.room_state = room_state
        self.states = None  # Need to update the states!
        self._calc_reward()  # Update variables like `self.boxes_on_target`

        # Compute returns
        done = self._check_if_done()
        observation = self.render(mode='raw')

        info = dict()
        if done:
            info["maxsteps_used"] = self._check_if_maxsteps()
            info["all_boxes_on_target"] = self._check_if_all_boxes_on_target()
            info["all_boxes_not_on_target"] = self._check_if_all_boxes_not_on_target()

        # Calculate reward
        self.reward_last = int(self._check_if_won())

        return observation, self.reward_last, done, info

    def reachable_states(self):
        """Return all the states reachable by macro-moves.
        """
        if self.states:  # States already computed
            return self.states

        raw = self.render(mode='raw')
        board, player = build_board_from_raw(raw)
        boxes = np.argwhere(
            (board == TYPE_LOOKUP['box on target']) |\
            (board == TYPE_LOOKUP['box not on target'])
        )

        states = []
        for box in boxes:
            # Generate all macro moves for this box
            for n_board, n_player in macro_moves(board, player, box, forward=self.forward):
                n_board[tuple(n_player)] = TYPE_LOOKUP['player']  # Place the player to create a valid room_state
                states.append(n_board)  # Add the macro-move

        self.states = states  # Save the computations for future calls
        return self.states

    def _check_if_all_boxes_not_on_target(self) -> bool:
        """True if all boxes are NOT on any target.
        This is the backward goal of the agent.
        """
        raw = self.render(mode='raw')
        board, _ = build_board_from_raw(raw)
        box_on_target_count = np.sum(board == TYPE_LOOKUP['box on target'])
        return box_on_target_count == 0

    def _check_if_won(self) -> bool:
        """Whether or not the game is won.
        Depends on the forward/backward mode.
        """
        forward_win = self.forward and self._check_if_all_boxes_on_target()
        backward_win = (not self.forward) and self._check_if_all_boxes_not_on_target()
        return forward_win or backward_win

    def _check_if_done(self) -> bool:
        """Done if all boxes are not on any target or
        the maximal steps have been reached.
        """
        return self._check_if_won() or self._check_if_maxsteps()


if __name__ == '__main__':
    print('Forward MacroSokobanEnv:')
    env = MacroSokobanEnv(forward=True, dim_room=(6, 6), num_boxes=2)
    raw = env.reset(render_mode='raw')
    board, player = build_board_from_raw(raw)
    print_board(board, player)

    moves = env.reachable_states()
    print('Number of macro moves:', len(moves))

    print('\nBackward MacroSokobanEnv:')
    env = MacroSokobanEnv(forward=False, dim_room=(6, 6), num_boxes=2)
    raw = env.reset(render_mode='raw')
    board, player = build_board_from_raw(raw)
    print_board(board, player)

    moves = env.reachable_states()
    print('Number of macro moves:', len(moves))
