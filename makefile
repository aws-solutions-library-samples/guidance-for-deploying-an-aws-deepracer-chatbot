ifndef config
override config = dev
endif

ifndef container
override container = finch
endif

.PHONY: test
test: backend.synth

backend.synth: export CDK_DOCKER=$(container)
backend.synth:	## Deploy via cdk
	npx cdk synth --all -c config=$(config) --require-approval never -c cdk_nag=true

.PHONY: diff
diff: backend.diff

backend.diff: export CDK_DOCKER=$(container)
backend.diff:	## Deploy via cdk
	npx cdk diff --all -c config=$(config) --require-approval never -c cdk_nag=false

.PHONY: deploy
deploy: all

.PHONY: all
all: backend.deploy create.config frontend.deploy frontend.invalidate.cache print.info

.PHONY: destroy
destroy: backend.destroy

bootstrap: export CDK_DOCKER=$(container)
bootstrap: ## Bootstrap environment
	npm install
	node ./scripts_n_helpers/updateCDKjson.mjs
	npx cdk bootstrap -c config=$(config) --require-approval never

backend.deploy: export CDK_DOCKER=$(container)
backend.deploy:	## Deploy via cdk
	npx cdk deploy --all -c config=$(config) --require-approval never --outputs-file outputs.json

backend.mainonly: export CDK_DOCKER=$(container)
backend.mainonly:	## Deploy via cdk
	npx cdk deploy --all -c config=$(config) --require-approval never --outputs-file outputs.json -c main_only=true

create.config:
	echo "Creating Config file"
	node ./scripts_n_helpers/generateConfig.mjs
	pushd ./lib/api/ && amplify codegen && popd

frontend.deploy: export BUCKETNAME=$(shell node ./scripts_n_helpers/getUserInterfaceBucketName.mjs)
frontend.deploy:
	cd lib/user_interface/nextjs-app && npm install && npx next build
	echo $(BUCKETNAME)
	aws s3 sync ./lib/user_interface/nextjs-app/out s3://$(BUCKETNAME)/ --delete --exclude 'access-logs/*'

frontend.invalidate.cache: export DISTRIBUTIONID=$(shell node ./scripts_n_helpers/getUserInterfaceDistributionId.mjs)
frontend.invalidate.cache:
	echo $(DISTRIBUTIONID)
	aws cloudfront create-invalidation --distribution-id $(DISTRIBUTIONID) --paths '/*'

backend.destroy: export CDK_DOCKER=$(container)
backend.destroy:	## Deploy via cdk
	npx cdk destroy --all -c config=$(config) --force

print.info:
	pushd ./scripts_n_helpers/ && npm install && popd
	node ./scripts_n_helpers/printEndOfMakeInfo.mjs
