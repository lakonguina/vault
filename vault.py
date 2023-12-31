import smartpy as sp

from fa2 import main
from fa2 import make_metadata


quipu_md = make_metadata(name="Quipu", decimals=8, symbol="QUIPU")
lp_md = make_metadata(name="vQuipu kUSD-USDt", decimals=8, symbol="vQuipu kUSD-USDt")

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
			token_b_address,
			token_lp_metadata,
		):
			main.Fa2FungibleMinimal.__init__(self, administrator, sp.big_map(), token_lp_metadata)

			self.data.pool_address = pool_address
			self.data.quipu_address = quipu_address
			self.data.quipu_amount = sp.nat(0)
            
			self.data.token_a = token_a_address
			self.data.token_b = token_b_address

			self.data.sell_token_a = sp.nat(0)
			self.data.sell_token_b = sp.nat(0)

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

			self.data.quipu_amount += amount
			
 			# Transfer quipu to me
			# Approve my token to dividend contract
			# Receive token & sell them for quipu
			# Add them to quipu pool

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

		admin = sp.test_account("Administrator")
		alice = sp.test_account("Alice")
		bob = sp.test_account("Robert")

		scenario = sp.test_scenario([main, main_bis])

		quipu = main.Fa2FungibleMinimal(
			admin.address,
			sp.big_map({
				(admin.address, sp.nat(0)):  sp.nat(100000000),
			}),
			quipu_md,
		) 

		dividend = main_bis.QuipuswapDividend()

		scenario += quipu
		scenario += dividend

		vault = main_bis.VaultQuipuswapDividend(
			admin.address,
			dividend.address,
			quipu.address,
			admin.address,
			admin.address,
			lp_md,
		)

		scenario += vault

		scenario.show(quipu.data)
		scenario.show("________________________________________")
		scenario.show("________________________________________")
		scenario.show(vault.data)
