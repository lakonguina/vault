import smartpy as sp

# FA2 standard: https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-12/tzip-12.md
# Documentation: https://smartpy.io/guides/FA2-lib/overview

@sp.module
def main():
		balance_of_args: type = sp.record(
				requests=sp.list[sp.record(owner=sp.address, token_id=sp.nat)],
				callback=sp.contract[
						sp.list[
								sp.record(
										request=sp.record(owner=sp.address, token_id=sp.nat), balance=sp.nat
								).layout(("request", "balance"))
						]
				],
		).layout(("requests", "callback"))
		
		class Fa2Function(sp.Contract):
			@sp.private(with_operations=True)
			def transfer_fa2(self, params):
				c = sp.contract(
					sp.list[
						sp.record(
							from_=sp.address,
							txs=sp.list[
								sp.record(
									to_=sp.address,
									token_id=sp.nat,
									amount=sp.nat
								).layout(("to_", ("token_id", "amount")))
							]
						).layout(("from_", "txs"))
					],
					params.address,
					entrypoint="transfer",
				).unwrap_some()

				sp.transfer(
					[
						sp.record(
							from_=params.from_,
							txs=[
								sp.record(
									to_=params.to,
									token_id=params.token_id,
									amount=params.amount,
								)
							]
						)
					],
					sp.tez(0),
					c,
				)

			@sp.private(with_operations=True)
			def approve_fa2(self, params):
				c = sp.contract(
					sp.list[
						sp.variant(
							add_operator=sp.record(
								owner=sp.address,
								operator=sp.address,
								token_id=sp.nat
							).layout(("owner", ("operator", "token_id"))),
							remove_operator=sp.record(
								owner=sp.address,
								operator=sp.address,
								token_id=sp.nat
							).layout(("owner", ("operator", "token_id")))
						)
					],
					params.address,
					entrypoint="update_operators",
				).unwrap_some()

				sp.transfer(
					[
						sp.variant.add_operator(sp.record(
							owner=params.owner,
							operator=params.operator,
							token_id=params.token_id,
						))
					],
					sp.tez(0),
					c,
				)

			@sp.private(with_operations=True)
			def get_balance_fa2(self, params):
				c = sp.contract(
					sp.record(
						callback = sp.contract[
							sp.list[
								sp.record(
									request=sp.record(
										owner=sp.address,
										token_id=sp.nat
									).layout(("owner", "token_id")),
									balance=sp.nat
								).layout(("request", "balance"))
							]
						],
						requests = sp.list[sp.record(owner=sp.address, token_id=sp.nat).layout(("owner", "token_id"))]
					),
					params.address,
					entrypoint="update_operators",
				).unwrap_some()

				sp.transfer(
					sp.record(
						callback = params.c,
						requests = [
							sp.record(
								owner=params.owner,
								token_id=params.token_id,
							)
						]
					),
					sp.tez(0),
					c,
				)


		class Fa2FungibleMinimal(sp.Contract):
				"""Minimal FA2 contract for fungible tokens.

				This is a minimal self contained implementation example showing how to
				implement an NFT following the FA2 standard in SmartPy. It is for
				illustrative purposes only. For a more flexible toolbox aimed at real world
				applications please refer to FA2_lib.
				"""

				def __init__(self, administrator, ledger, metadata):
						self.data.administrator = administrator
						self.data.ledger = sp.cast(
								ledger, sp.big_map[sp.pair[sp.address, sp.nat], sp.nat]
						)
						self.data.metadata = metadata
						self.data.operators = sp.cast(
								sp.big_map(),
								sp.big_map[
										sp.record(
												owner=sp.address,
												operator=sp.address,
												token_id=sp.nat,
										).layout(("owner", ("operator", "token_id"))),
										sp.unit,
								],
						)
						self.data.supply = sp.cast(sp.big_map(), sp.big_map[sp.nat, sp.nat])
						self.data.token_metadata = sp.cast(
								sp.big_map(),
								sp.big_map[
										sp.nat,
										sp.record(token_id=sp.nat, token_info=sp.map[sp.string, sp.bytes]),
								],
						)

				@sp.entrypoint
				def transfer(self, batch):
						"""Accept a list of transfer operations.

						Each transfer operation specifies a source: `from_` and a list
						of transactions. Each transaction specifies the destination: `to_`,
						the `token_id` and the `amount` to be transferred.

						Args:
								batch: List of transfer operations.
						Raises:
								`FA2_TOKEN_UNDEFINED`, `FA2_NOT_OPERATOR`, `FA2_INSUFFICIENT_BALANCE`
						"""
						for transfer in batch:
								for tx in transfer.txs:
										sp.cast(
												tx,
												sp.record(
														to_=sp.address, token_id=sp.nat, amount=sp.nat
												).layout(("to_", ("token_id", "amount"))),
										)
										from_ = (transfer.from_, tx.token_id)
										to_ = (tx.to_, tx.token_id)
										assert transfer.from_ == sp.sender or self.data.operators.contains(
												sp.record(
														owner=transfer.from_,
														operator=sp.sender,
														token_id=tx.token_id,
												)
										), "FA2_NOT_OPERATOR"
										self.data.ledger[from_] = sp.as_nat(
												self.data.ledger.get(from_, default=0) - tx.amount,
												error="FA2_INSUFFICIENT_BALANCE",
										)
										self.data.ledger[to_] = (
												self.data.ledger.get(to_, default=0) + tx.amount
										)

				@sp.entrypoint
				def update_operators(self, actions):
						"""Accept a list of variants to add or remove operators.

						Operators can perform transfer on behalf of the owner.
						Owner is a Tezos address which can hold tokens.

						Only the owner can change its operators.

						Args:
								actions: List of operator update actions.
						Raises:
								`FA2_NOT_OWNER`
						"""
						for action in actions:
								with sp.match(action):
										with sp.case.add_operator as operator:
												assert operator.owner == sp.sender, "FA2_NOT_OWNER"
												self.data.operators[operator] = ()
										with sp.case.remove_operator as operator:
												assert operator.owner == sp.sender, "FA2_NOT_OWNER"
												del self.data.operators[operator]

				@sp.entrypoint
				def balance_of(self, param):
						"""Send the balance of multiple account / token pairs to a
						callback address.

						transfer 0 mutez to `callback` with corresponding response.

						Args:
								callback (contract): Where we callback the answer.
								requests: List of requested balances.
						Raises:
								`FA2_TOKEN_UNDEFINED`, `FA2_CALLBACK_NOT_FOUND`
						"""
						sp.cast(param, balance_of_args)
						balances = []
						for req in param.requests:
								balances.push(
										sp.record(
												request=sp.record(owner=req.owner, token_id=req.token_id),
												balance=self.data.ledger.get(
														(req.owner, req.token_id), default=0
												),
										)
								)

						sp.transfer(reversed(balances), sp.mutez(0), param.callback)

				@sp.offchain_view
				def all_tokens(self):
						"""(Offchain view) Return the list of all the `token_id` known to the contract."""
						return [sp.nat(0)]

				@sp.offchain_view
				def get_balance(self, params):
						"""(Offchain view) Return the balance of an address for the specified `token_id`."""
						sp.cast(
								params,
								sp.record(owner=sp.address, token_id=sp.nat).layout(
										("owner", "token_id")
								),
						)
						return self.data.ledger.get((params.owner, params.token_id), default=0)

				@sp.offchain_view
				def total_supply(self, params):
						"""(Offchain view) Return the total number of tokens for the given `token_id` if known or
						fail if not."""
						return self.data.supply.get(params.token_id, default=0)

				@sp.offchain_view
				def is_operator(self, params):
					"""(Offchain view) Return whether `operator` is allowed to transfer `token_id` tokens owned by `owner`."""
					return self.data.operators.contains(params)


def make_metadata(symbol, name, decimals):
	return sp.map(
		l={
			"decimals": sp.utils.bytes_of_string("%d" % decimals),
			"name": sp.utils.bytes_of_string(name),
			"symbol": sp.utils.bytes_of_string(symbol),
		}
	)

