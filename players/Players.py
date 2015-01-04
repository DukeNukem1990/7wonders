
#!/usr/bin/python
#
# Copyright 2015 - Jonathan Gordon
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
# KIND, either express or implied.

from collections import deque
from sys import stdin
from common import *
import cards

class Player:
	def __init__(self, name):
		self.name = name
		self.money = 3
		self.tableau = [] # all the players played cards
		self.military = [] # war wins/losses
		self.east_trade_prices = {
			RESOURCE_WOOD: 2,
			RESOURCE_ORE: 2,
			RESOURCE_STONE: 2,
			RESOURCE_BRICK: 2,
			RESOURCE_GLASS: 2,
			RESOURCE_LOOM: 2,
			RESOURCE_PAPER: 2
		}
		self.west_trade_prices = self.east_trade_prices.copy()
		self.wonder = None
	
	def get_cards(self):
		return self.tableau
	
	def play_hand(self, hand):
		''' return the card and action done'''
		options = []
		for card in hand:
		#	print card, self.is_card_in_tableau(card), self.buy_card(card, [], [])
			if not self.is_card_in_tableau(card):
				if self.can_build_with_chain(card):
					options.append((ACTION_PLAYCARD, card))
				elif self.buy_card(card, [], []):
					options.append((ACTION_PLAYCARD, card))
			options.append((ACTION_DISCARD, card))
			if False:#self.wonder.built_stages < 3: #FIXMEself.wonder.stages:
				options.append((ACTION_STAGEWONDER, card))
		i = 0
		print "-=================-"
		
		options = sorted(options, key=lambda x: {CARDS_GREY:0, CARDS_BROWN:1, CARDS_YELLOW:2, CARDS_BLUE:3, CARDS_RED:4, CARDS_GREEN:5, CARDS_PURPLE:6}[x[1].get_colour()])
		for o in options:
			actions = { ACTION_PLAYCARD:"Play", ACTION_DISCARD:"Discard", ACTION_STAGEWONDER:"Stage" }
			print "[%d]: %s %s" % (i, actions[o[0]], o[1].pretty_print_name())
			i += 1
		print "-=================-"
		
		userinput = int(stdin.readline())
		return options[userinput]
	
	def print_tableau(self):
		cards = { CARDS_BROWN:[], CARDS_GREY:[], CARDS_YELLOW:[], CARDS_BLUE:[], CARDS_RED:[], CARDS_GREEN:[], CARDS_PURPLE:[] }
		print "You have $%d" % (self.money)
		for c in self.get_cards():
			cards[c.get_colour()].append(c)
		
		biggest_deck = 0
		for colour in cards.keys():
			count =  len(cards[colour])
			if count > biggest_deck:
				biggest_deck = count
		for i in range(biggest_deck):
			line = { CARDS_BROWN:"\t", CARDS_GREY:"\t", CARDS_YELLOW:"\t", CARDS_BLUE:"\t", CARDS_RED:"\t", CARDS_GREEN:"\t", CARDS_PURPLE:"\t" }
			for colour in [CARDS_BROWN, CARDS_GREY, CARDS_YELLOW, CARDS_BLUE, CARDS_RED, CARDS_GREEN, CARDS_PURPLE]:
				if len(cards[colour]) > biggest_deck - 1 - i:
					line[colour] = cards[colour][biggest_deck - 1 - i].pretty_print_name()
				else:
					line[colour] = "        "
			
			print "%s\t%s\t%s\t%s\t%s\t%s\t%s" % ( line[CARDS_BROWN], line[CARDS_GREY], line[CARDS_YELLOW], line[CARDS_BLUE], line[CARDS_RED], line[CARDS_GREEN],line[CARDS_PURPLE])
		
	
	def set_wonder(self, wonder):
		self.wonder = wonder
	
	def is_card_in_tableau(self, card):
		return find_card(self.get_cards(), card) != None

	def can_build_with_chain(self, card):
		for precard in card.prechains:
			if find_card(self.get_cards(), precard):
				return True
		return False
		
	def buy_card(self, card, east_player, west_player):
		missing = []
		money_spent = 0
		trade_east = 0
		trade_west = 0
		options = []
		if len(card.cost) == 0:
			return CardPurchaseOption([], 0, [], [])
		for i in range(len(card.cost)):
			cost = deque(card.cost)
			cost.rotate(i)
			x = self._find_resource_cards(list(cost), east_player, west_player, True)
			if x and x not in options:
					options.append(x)
			x = self._find_resource_cards(list(cost), east_player, west_player, False)
			if x and x not in options:
					options.append(x)
		# we now remove any of the optoins which we cant afford to pay for trades
		for o in options:
			cost = o.coins
			for c in o.east_trades:
				cost += self.east_trade_prices[c.get_info()[0]]
			for c in o.east_trades:
				cost += self.west_trade_prices[c.get_info()[0]]
			if cost > self.money:
				options.remove(o)
		return options

	def _find_resource_cards(self, needed_resources, east_cards, west_cards, east_first=True):
		def __check_tableau(r, tableau, used_cards):
			for c in tableau: # FIXME: WONDER too
				if c not in used_cards and (c.get_colour() == CARDS_BROWN or c.get_colour() == CARDS_GREY):
					count = c.provides_resource(r)
					if count == 0:
						continue
					return (c, count)
			return (None, 0)

		used_cards = []
		coins = 0
		east_trades = []
		west_trades = []
		card_sets = [(self.get_cards(), used_cards)]
		if east_first:
			card_sets += [(east_cards, east_trades), (west_cards, west_trades)]
		else:
			card_sets += [(west_cards, west_trades), (east_cards, east_trades)]
		
		while len(needed_resources):
			r = needed_resources[0]
			found = False
			if r == RESOURCE_MONEY:
				coins += 1
				needed_resources.remove(r)
				continue
			for cards, used in card_sets:
				card, count = __check_tableau(r, cards, used)
				if card and count > 0:
					found = True
					used.append(card)
					for i in range(0, count):
						if r not in needed_resources:
							break
						needed_resources.remove(r)
					break
			if not found:
				return None
		return CardPurchaseOption(used_cards, coins, east_trades, west_trades)
							
			
class CardPurchaseOption:
	def __init__(self, cards, coins, east_trades, west_trades):
		self.cards = cards
		self.coins = coins
		self.east_trades = east_trades
		self.west_trades = west_trades

	def __eq__(self, other):
		return sort_cards(self.cards) == sort_cards(other.cards) and \
			self.coins == other.coins and	\
			sort_cards(self.east_trades) == sort_cards(other.east_trades) and	\
			sort_cards(self.west_trades) == sort_cards(other.west_trades)

	def __repr__(self):
		return "{\n\t%s\n\t$%d\n\tEAST:%s\n\tWEST:%s\n}" % (self.cards, self.coins, self.east_trades, self.west_trades)
