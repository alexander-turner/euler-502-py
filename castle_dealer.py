import castle as cstl  # frees the variable name "castle"
import copy
import tabulate


class CastleDealer:

    def run(self, max_height, max_width):
        """Initializes bounds so we know up to what point cached moves should be prepared.

        :param max_height: the maximum Castle height that will be used
        :param max_width: the maximum Castle width that will be used
        """
        self.max_height, self.max_width = max_height, max_width

        self.cache_moves()
        self.castle_results = {}  # castle_results[castle] = number of even- and odd-blocked solutions
        self.block_number_results = {}  # question what do es this do

        self.iterate_castles()

    def cache_moves(self):
        # cached_moves[i] contains the moves available for a space of size i that weren't available for k < i
        self.cached_moves = [[] for _ in range(self.max_width + 1)]
        for move_size in range(1, self.max_width + 1):  # each valid size
            for move_index in range(self.max_width + 1 - move_size):  # each valid index
                self.cached_moves[move_size].append(cstl.Block(move_index, move_size))

    def iterate_castles(self):
        """Iterate Castles up to (max_height, max_width) and display results."""
        print("Iterating over castle sizes (dimensions not exceeding {} by {}).".format(self.max_height,
                                                                                        self.max_width))
        print("Results format: {solutions with even blocks, solutions with odd blocks}")

        table = []
        for width in range(1, self.max_width + 1):
            new_row = [width]
            for height in range(1, self.max_height + 1):
                self.global_castle = cstl.Castle(height, width)  # TODO fix confusing reversal?
                """
                For castles with height = 1, the result is {0, 1}.
                For castles where width = 1, the result is {(height + 1) % 2, height % 2}.
                """
                result = self.solve_castle(0)
                new_row.append(result)
                self.castle_results[self.global_castle] = result

            table.append(new_row)
        headers = ["width \ height"]
        headers += list(range(1, self.max_height + 1))
        print(tabulate.tabulate(table, headers, tablefmt="grid"))

    def solve_castle(self, space_index):
        """Recursively enumerate Castles using global_castle.

        :param space_index: global_castle.spaces[global_castle.current_row][space_index] is currently being operated on.
        :return result: list containing the number of even- and odd-block-numbered castles matching the given criteria.
        """
        result = [0, 0]
        castle = self.global_castle  # nickname

        if castle.last_row_has_blocks():
            # Mark how solutions are distributed across number of blocks used
            # self.block_number_results[self.global_castle] += 1  # TODO fix
            if castle.last_id_even():
                result[0] += 1
            else:
                result[1] += 1

        if castle.can_add_block():
            for space_index in range(space_index,  # for each remaining space in the current row
                                     len(castle.spaces[castle.current_row])):
                space = castle.spaces[castle.current_row][space_index]
                for move_width in range(1, space.width + 1):
                    for move_index in range(space.width - move_width):
                        move = copy.copy(self.cached_moves[move_width][move_index])
                        move.index += space.index  # increment by current index; cached_moves doesn't account for offset

                        last_space_index = castle.place_block_update(move, space_index)

                        if castle.skip_space:  # leave current space alone and proceed to next in list (branching)
                            castle.skip_space = False
                            result = [sum(x) for x in zip(result, self.solve_castle(last_space_index + 1))]
                        else:
                            result = [sum(x) for x in zip(result, self.solve_castle(last_space_index))]

                        castle.remove_block_update(move, last_space_index)

        if castle.can_advance():
            castle.advance_row()
            result = [sum(x) for x in zip(result, self.solve_castle(0))]
            castle.retreat_row()

        return result