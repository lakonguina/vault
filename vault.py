import smartpy as sp

from fa2 import main
from fa2 import make_metadata


quipu_md = make_metadata(name="Quipu", decimals=8, symbol="QUIPU")
lp_md = make_metadata(name="vQuipu kUSD-USDt", decimals=8, symbol="vQuipu kUSD-USDt")

@sp.module
def main_bis():
	class QuipuswapDividend(
		main.Fa2Function,
	):
		def __init__(self, quipu_address):
			main.Fa2Function.__init__(self)

			self.data.quipu_address = quipu_address
 
		@sp.entrypoint
		def add(self, params):
			sp.cast(params, sp.record(amount=sp.nat, pool_id=sp.nat))	
 			# Transfer quipu to me
			self.transfer_fa2(
				sp.record(
					from_ = sp.sender,
					to = sp.self_address(),
					address = self.data.quipu_address,
					token_id = sp.nat(0),
					amount = params.amount
				)
			)
 
		@sp.entrypoint
		def remove(self):
			pass

	class VaultQuipuswapDividend(
		main.Fa2FungibleMinimal,
		main.Fa2Function,
	):
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
			main.Fa2Function.__init__(self)

			self.data.pool_address = pool_address
			self.data.pool_id = sp.nat(0)
			self.data.quipu_address = quipu_address
			self.data.quipu_amount = sp.nat(0)
            
			self.data.token_a = token_a_address
			self.data.token_b = token_b_address
			self.data.token_a_id = sp.nat(0)
			self.data.token_b_id = sp.nat(0)
			self.data.token_a_balance = sp.nat(0)
			self.data.token_b_balance = sp.nat(0)

			self.data.sell_token_a = sp.nat(0)
			self.data.sell_token_b = sp.nat(0)

		@sp.private(with_operations=True)
		def call_add(self, params):
			c = sp.contract(
				sp.record(
					pool_id=sp.nat,
					amount=sp.nat,
				),
				params.address,
				entrypoint="add",
			).unwrap_some()

			sp.transfer(
				sp.record(
					pool_id=params.pool_id,
					amount=params.amount,
				),
				sp.tez(0),
				c,
			)

		@sp.entrypoint
		def balance(self, params):
			sp.cast(
				params,
				sp.list[
					sp.record(
						request=sp.record(
							owner=sp.address,
							token_id=sp.nat
						).layout(("owner", "token_id")),
						balance=sp.nat
					).layout(("request", "balance"))
				]
			)

		@sp.entrypoint
		def stake(self, amount):
			if self.data.supply.get(sp.nat(0), default=sp.nat(0)) == sp.nat(0):
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
			self.transfer_fa2(
				sp.record(
					from_ = sp.sender,
					to = sp.self_address(),
					address = self.data.quipu_address,
					token_id = sp.nat(0),
					amount = amount
				)
			)

			# Approve my token to dividend contract
			self.approve_fa2(
				sp.record(
					operator=self.data.pool_address,
					owner=sp.self_address(),
					address=self.data.quipu_address,	
					token_id=sp.nat(0)
				)
			)

			# Add them to quipu pool
			self.call_add(sp.record(
				address=self.data.pool_address,
				amount=amount,
				pool_id=self.data.pool_id,
			))

			# Get balance 
			self.get_balance_fa2(sp.record(
				c=sp.self_entrypoint("balance"),
				address=self.data.token_a,
				owner=sp.self_address(),
				token_id=self.data.token_a_id		
			))
		
			# Receive token & sell them for quipu
			

			# Stake quipu sold

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

		scenario += quipu

		dividend = main_bis.QuipuswapDividend(quipu.address)

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
		
		token_a = main.Fa2FungibleMinimal(
			admin.address,
			sp.big_map({
				(vault.address, sp.nat(0)):  sp.nat(1000),
			}),
			quipu_md,
		) 

		token_b = main.Fa2FungibleMinimal(
			admin.address,
			sp.big_map({
				(vault.address, sp.nat(0)):  sp.nat(1000),
			}),
			quipu_md,
		) 
		
		scenario += token_a
		scenario += token_b

		quipu_amount = sp.nat(100000000)
		quipu.update_operators([
			sp.variant("add_operator",
				sp.record(
					owner=admin.address,
					operator=vault.address,
					token_id=sp.nat(0),
				)
			)
		]).run(sender=admin)

		vault.stake(quipu_amount).run(sender=admin)

		scenario.show(vault.data.ledger)
		scenario.verify(vault.data.quipu_amount == quipu_amount)
		scenario.verify(vault.data.supply[sp.nat(0)] == 1000000)
		scenario.verify(vault.data.ledger[(admin.address, sp.nat(0))] == 1000000)
		scenario.verify(quipu.data.ledger[(dividend.address, sp.nat(0))] == quipu_amount)
