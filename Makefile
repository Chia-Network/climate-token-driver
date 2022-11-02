# import tests from submodule `chia-blockchain`
PY = PYTHONPATH=$(PYTHONPATH):./chia-blockchain:. python
PYTEST = $(PY) -m pytest
PYINSTALLER = pyinstaller --clean
CHIALISP_DIR = ./app/core/chialisp
RUN = run --include $(CHIALISP_DIR)
OPC = opc

clsp_target_for_coin = $(1).min.clsp $(1).clsp.hex $(1).clsp.hex.sha256tree
clsp_target_for_scheme = $(foreach target,$(2),$(call clsp_target_for_coin,$(1)/$(target)))

.PRECIOUS: %.min.clsp %.clsp.hex %.clsp.hex.sha256tree

%.min.clsp: %.clsp
	$(RUN) $^ > $@

%.clsp.hex: %.min.clsp
	$(OPC) $^ > $@

%.clsp.hex.sha256tree: %.min.clsp
	$(OPC) --script-hash $^ > $@

targets = $(call clsp_target_for_scheme,$(CHIALISP_DIR),\
	delegated_tail_with_index \
	mint_with_signature \
	melt_all_with_signature \
	melt_all_by_anyone \
	gateway_with_conditions \
)

.PHONY: clean-clvm
clean-clvm:
	rm $(targets)

.PHONY: compile-clvm
compile-clvm: $(targets)

.PHONY: test-app
test-app:
	@$(PYTEST) ./tests

.PHONY: package-app
package-app: ## package python app via pyinstaller
	@$(PYINSTALLER) pyinstaller.spec
