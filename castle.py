class Castle:
    """A robust interface for generating and manipulating Castles."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.block_grid = [[False] * self.width for _ in range(self.height)]

        # Initialize record-keeping data-structures
        self.unavailable_column = [False] * self.width  # columns where we can't build without making an overhang
        self.placed_in_row = [0] * self.height
        self.spaces = [[] for _ in range(self.height)]  # spaces at each level of the castle
        
        self.last_id = 0  # ID of the last block placed
        self.current_row = 0  # current level we're working on
        # If we've already processed all permutations created by placing a block in space
        self.skip_space = False

        # Place first space and block
        self.spaces[self.current_row].append(Block(0, self.width))  # "block" of empty space
        self.place_block(Block(0, self.width), 0)

        # Leave the first row
        if self.can_advance():
            self.advance_row()

    def place_block(self, block, space_index):
        """Robust block placement.

        :param block:
        :param space_index: the space currently being operated in is self.spaces[self.current_row][space_index].
        :return new_index: index of left space created by the displacement move causes in the space.
                 If no spaces remain, -1 is returned.
        """
        left_side, right_side = block.index - 1, block.index + block.width

        # Lay the block
        self.last_id += 1

        self.block_grid[self.current_row][block.index:right_side] = [True] * (right_side - block.index)
        self.placed_in_row[self.current_row] += 1

        # Mark sides as unavailable
        if left_side >= 0:
            self.unavailable_column[left_side] = True
        if right_side < self.width:
            self.unavailable_column[right_side] = True

        # We can now build on top of the block
        self.add_space_above(block)

        space = self.spaces[self.current_row].pop(space_index)

        # Indicate whether we have to perform additional book-keeping on spaces to the sides of the block
        modify_left = left_side > space.index
        modify_right = right_side + 1 < space.index + space.width  # if space ends past the block's right end
        new_index = space_index

        # Modify the current row's spaces
        if modify_left:
            self.spaces[self.current_row].insert(space_index, Block(space.index, left_side - space.index))
            space_index += 1
            self.skip_space = True

        if modify_right:  # TODO inserts take O(n) in worst case; find better DS
            self.spaces[self.current_row].insert(space_index,
                                                 Block(right_side + 1, space.index + space.width - right_side - 1))

        return new_index

    def remove_block(self, block, space_index):
        """Removes the specified block and merges any relevant space(s).

        :param block:
        :param space_index: the space in question is self.spaces[self.current_row][space_index].
        """
        left_side, right_side = block.index - 1, block.index + block.width
        left_in_bounds, right_in_bounds, left_space_free, right_space_free, \
            block_to_left, block_to_right, left_overhang, right_overhang, \
            increment_left, decrement_right = self.get_booleans(block)

        # Remove the block
        self.last_id -= 1
        self.block_grid[self.current_row][block.index:right_side] = [False] * (right_side - block.index)

        # Remove space above
        self.remove_space_above()
        self.placed_in_row[self.current_row] -= 1

        # Mark as available if the removed block was why the column wasn't available
        if left_in_bounds and not block_to_left and not left_overhang:
            self.unavailable_column[left_side] = False
        if right_in_bounds and not block_to_right and not right_overhang:
            self.unavailable_column[right_side] = False

        # Adjust dimensions of soon-to-be-added space
        if increment_left:
            left_side += 1
        if decrement_right:
            right_side -= 1

        # Increment width because if left bound == right bound == 0, it's a one-width block
        new_space = Block(left_side, right_side - left_side + 1)

        if left_space_free:  # merge with space on the left
            left_space = self.spaces[self.current_row].pop(space_index)
            new_space = Block(left_space.index, new_space.width + left_space.width)

        if right_space_free:  # merge with space on the right
            right_space = self.spaces[self.current_row].pop(space_index)
            new_space.width += right_space.width

        # Add the space
        self.spaces[self.current_row].insert(space_index, new_space)

    def get_booleans(self, block):
        """Return a tuple of booleans concerning the surroundings of the given block.

        :return left_in_bounds, right_in_bounds: are the indices immediately neighboring block in-bounds?
        :return left_space_free, right_space_free: is there a space two indices away from the given side of block?
        :return block_to_left, block_to_right: is there a block two indices away from the given side of block?
        :return left_overhang, right_overhang: would building one square to the side create an overhang?
        :return increment_left, decrement_right: should we narrow our estimate of the free space that will be created by
         removing block?
        """
        left_side, right_side = block.index - 1, block.index + block.width
        left_in_bounds, right_in_bounds = left_side > 0, right_side < self.width
        left_space_free, right_space_free, block_to_left, block_to_right, left_overhang, right_overhang = [False] * 6

        if left_in_bounds:
            left_overhang = not self.block_grid[self.current_row - 1][left_side]  # true if nothing is to the left
            if left_side > 0:  # if two squares to the left is in-bounds
                block_to_left = self.block_grid[self.current_row][left_side - 1]
                left_space_free = not left_overhang and not block_to_left and not self.unavailable_column[left_side - 1]

        if right_in_bounds:
            right_overhang = not self.block_grid[self.current_row - 1][right_side]
            if right_side < self.width - 1:  # if two squares to the right is in-bounds
                block_to_right = self.block_grid[self.current_row][right_side + 1]
                right_space_free = not right_overhang and not block_to_right and \
                    not self.unavailable_column[right_side + 1]

        increment_left = left_overhang or not left_in_bounds or block_to_left
        decrement_right = right_overhang or not right_in_bounds or block_to_right

        return left_in_bounds, right_in_bounds, left_space_free, right_space_free, block_to_left, block_to_right, \
            left_overhang, right_overhang, increment_left, decrement_right

    def add_space_above(self, space):
        """Add a space to the next row, if there is one.

        :param space: a Block; the move being executed.
        """
        if self.in_last_row():
            return
        self.spaces[self.current_row + 1].append(space)

    def remove_space_above(self):
        """Remove the last space from the next row, if there is one."""
        if self.in_last_row():
            return
        self.spaces[self.current_row + 1].pop()

    def advance_row(self):
        self.current_row += 1

    def retreat_row(self):
        self.current_row -= 1

    def last_id_even(self):
        """True if the last block ID was even."""
        return (self.last_id - 1) % 2 == 0

    def last_row_has_blocks(self):
        return self.placed_in_row[-1] > 0

    def in_last_row(self):
        return self.current_row == self.height - 1

    def is_even_solution(self):
        return self.last_row_has_blocks() and self.last_id_even()

    def can_add_block(self):
        return self.spaces[self.current_row]

    def can_advance(self):
        """Can start building the next level of the Castle."""
        return not self.in_last_row() and self.placed_in_row[self.current_row] > 0

    def __repr__(self):
        output = ''
        for row in range(self.height - 1, -1, -1):
            row_str = ''
            for col in range(self.width):
                row_str += ('░', '█')[self.block_grid[row][col]]
            output += row_str + (' <' if row == self.current_row else '') + '\n'
        return output


class Block:
    def __init__(self, index, width):
        """Demarcates the starting column and width of a block.

        :param index: column where the left edge of the space begins.
        """
        self.index = index
        self.width = width

    def __repr__(self):
        print("[index: {}, width: {}]".format(self.index, self.width))
