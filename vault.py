import smartpy as sp

from fa2 import main

@sp.module
def main_bis():
	class QuipuswapDividend(sp.Contract):
		def __init__(self):
			pass
 
		@sp.entrypoint
		def add(self):
			pass
 
		@sp.entrypoint
		def remove(self):
			pass

	class VaultQuipuswapDividend(main.Fa2FungibleMinimal):
		def __init__(
			self,
			administrator,
			pool_address,
			quipu_address,
			token_a_address,
			token_a_type,
			token_b_address,
			token_b_type,
		):
			main.Fa2FungibleMinimal.__init__(self, administrator, {}) 

			self.data.pool_address = pool_address
			self.data.quipu_address = quipu_address
			self.data.quipu_amount = sp.nat(0)
            
			self.data.token_a = sp.record(
				address = token_a_address,
				type_ = token_a_type,
			)
 
			self.data.token_b = sp.record(
				address = token_b_address,
				type_ = token_b_type,
			)

		@sp.entrypoint
		def stake(self, amount):
			if self.data.supply[sp.nat(0)] == sp.nat(0):
				# Update vToken
				shares = 1000000

				self.data.supply[sp.nat(0)] = shares
				self.data.ledger[(sp.sender, sp.nat(0))] = shares
				
				# Update Quipu balance
			else:
				shares = (amount * self.data.supply[sp.nat(0)]) / self.data.quipu_amount

				self.data.supply[sp.nat(0)] += shares
				self.data.ledger[(sp.sender, sp.nat(0))] += shares

			self.data.quipu_amount 	+= amount

		@sp.entrypoint
		def unstake(self):
			pass

		@sp.entrypoint
		def set_owner(self, administrator):
			assert sp.sender == self.data.administrator
			self.data.administrator = administrator


if "templates" not in __name__:
	@sp.add_test(name="StoreValue")
	def test():
		c1 = main_bis.QuipuswapDividend()
		scenario = sp.test_scenario([main, main_bis])
		scenario.h1("Store Value")
		scenario += c1
