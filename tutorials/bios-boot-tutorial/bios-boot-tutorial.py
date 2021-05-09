#!/usr/bin/env python3

import argparse
import json
import numpy
import os
import random
import re
import subprocess
import sys
import time

args = None
logFile = None

unlockTimeout = 999999999
fastUnstakeSystem = '../../eosio.contracts/build/contracts/eosio.systemnew/eosio.system.wasm'
#fastUnstakeSystem = './replace.json'

systemAccounts = [
    'vex.bpay',
    'vex.msig',
    'vex.names',
    'vex.ram',
    'vex.ramfee',
    'vex.saving',
    'vex.stake',
    'vex.token',
    'vex.vpay',
    'vex.rex',
]

def jsonArg(a):
    return " '" + json.dumps(a) + "' "

def run(args):
    print('bios-boot-tutorial.py:', args)
    logFile.write(args + '\n')
    if subprocess.call(args, shell=True):
        print('bios-boot-tutorial.py: exiting because of error')
        sys.exit(1)

def retry(args):
    while True:
        print('bios-boot-tutorial.py:', args)
        logFile.write(args + '\n')
        if subprocess.call(args, shell=True):
            print('*** Retry')
        else:
            break

def background(args):
    print('bios-boot-tutorial.py:', args)
    logFile.write(args + '\n')
    return subprocess.Popen(args, shell=True)

def getOutput(args):
    print('bios-boot-tutorial.py:', args)
    logFile.write(args + '\n')
    proc = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE)
    return proc.communicate()[0].decode('utf-8')

def getJsonOutput(args):
    return json.loads(getOutput(args))

def sleep(t):
    print('sleep', t, '...')
    time.sleep(t)
    print('resume')

def startWallet():
    run('rm -rf ' + os.path.abspath(args.wallet_dir))
    run('mkdir -p ' + os.path.abspath(args.wallet_dir))
    background(args.keosd + ' --unlock-timeout %d --http-server-address 127.0.0.1:6666 --wallet-dir %s' % (unlockTimeout, os.path.abspath(args.wallet_dir)))
    sleep(.4)
    run(args.cleos + 'wallet create -f password.txt')#--to-console

def importKeys():
    run(args.cleos + 'wallet import --private-key ' + args.private_key)
    keys = {}
    for a in accounts:
        key = a['pvt']
        if not key in keys:
            if len(keys) >= args.max_user_keys:
                break
            keys[key] = True
            run(args.cleos + 'wallet import --private-key ' + key)
    for i in range(firstProducer, firstProducer + numProducers):
        a = accounts[i]
        key = a['pvt']
        if not key in keys:
            keys[key] = True
            run(args.cleos + 'wallet import --private-key ' + key)

def startNode(nodeIndex, account):
    dir = args.nodes_dir + ('%02d-' % nodeIndex) + account['name'] + '/'
    run('rm -rf ' + dir)
    run('mkdir -p ' + dir)
    otherOpts = ''.join(list(map(lambda i: '    --p2p-peer-address localhost:' + str(9000 + i), range(nodeIndex))))
    if not nodeIndex: otherOpts += (
        '    --plugin eosio::history_plugin'
        '    --plugin eosio::history_api_plugin'
    )
    cmd = (
        args.nodeos +
        '    --max-irreversible-block-age -1'
        '    --contracts-console'
        '    --genesis-json ' + os.path.abspath(args.genesis) +
        '    --blocks-dir ' + os.path.abspath(dir) + '/blocks'
        '    --config-dir ' + os.path.abspath(dir) +
        '    --data-dir ' + os.path.abspath(dir) +
        '    --chain-state-db-size-mb 1024'
        '    --http-server-address 127.0.0.1:' + str(8000 + nodeIndex) +
        '    --p2p-listen-endpoint 127.0.0.1:' + str(9000 + nodeIndex) +
        '    --max-clients ' + str(maxClients) +
        '    --p2p-max-nodes-per-host ' + str(maxClients) +
        '    --enable-stale-production'
        '    --producer-name ' + account['name'] +
        '    --private-key \'["' + account['pub'] + '","' + account['pvt'] + '"]\''
        '    --plugin eosio::http_plugin'
        '    --plugin eosio::chain_api_plugin'
        '    --plugin eosio::producer_plugin' +
        otherOpts)
    with open(dir + 'stderr', mode='w') as f:
        f.write(cmd + '\n\n')
    background(cmd + '    2>>' + dir + 'stderr')

def startOneNode(nodeIndex, account):
    dir = args.nodes_dir + ('%02d-' % nodeIndex) + account['name'] + '/'
    run('rm -rf ' + dir)
    run('mkdir -p ' + dir)
    otherOpts = ''.join(list(map(lambda i: '    --p2p-peer-address localhost:' + str(9000 + i), range(nodeIndex)))) 
    # if not nodeIndex: otherOpts += (
    #     '    --plugin eosio::history_plugin'
    #     '    --plugin eosio::history_api_plugin'
    # )

    bpnames = ''
    bpsigpros = ''
    for i in range(0, numProducers):
        bpaccount = bpaccounts[i]
        bpnames =  bpnames + bpaccount['name'] + '  '
        bpsigpros = bpsigpros + bpaccount['pub'] + '=KEY:' + bpaccount['pvt'] + '  '  
    # print('bpaccounts ', bpnames)
    # print('bpsigpros ', bpsigpros)
    
    cmd = (
        args.nodeos +
        '    --max-irreversible-block-age -1'
        '    --contracts-console'
        '    --genesis-json ' + os.path.abspath(args.genesis) +
        '    --blocks-dir ' + os.path.abspath(dir) + '/blocks'
        '    --config-dir ' + os.path.abspath(dir) +
        '    --data-dir ' + os.path.abspath(dir) +
        '    --chain-state-db-size-mb 1024'
        '    --http-server-address 127.0.0.1:' + str(8000 + nodeIndex) +
        '    --p2p-listen-endpoint 127.0.0.1:' + str(9000 + nodeIndex) +
        '    --max-clients ' + str(maxClients) +
        '    --p2p-max-nodes-per-host ' + str(maxClients) +
        '    --enable-stale-production'
        '    --producer-name ' + "".join('%s' %id for id in bpnames) +
        '    --signature-provider=' + "".join('%s' %id for id in bpsigpros) +
        '    --plugin eosio::http_plugin'
        '    --plugin eosio::chain_api_plugin'
        '    --plugin eosio::producer_plugin' +
        otherOpts)
    with open(dir + 'stderr', mode='w') as f:
        f.write(cmd + '\n\n')
    background(cmd + '    2>>' + dir + 'stderr')	

def startProducers(b, e):
    # for i in range(b, e):
    #     startNode(i - b + 1, accounts[i])
    for i in range(0, 1):
        startOneNode(i + 1, bpaccounts[i])


def createSystemAccounts():
    for a in systemAccounts:
        run(args.cleos + 'create account vexcore ' + a + ' ' + args.public_key)
        #sleep(1.0)

def intToCurrency(i):
    return '%d.%04d %s' % (i // 10000, i % 10000, args.symbol)

def allocateFunds(b, e):
    # dist = numpy.random.pareto(1.161, e - b).tolist() # 1.161 = 80/20 rule
    # dist.sort()
    # dist.reverse()
    # factor = 1_000_000_000 / sum(dist)
    # total = 0
    # for i in range(b, e):
    #     funds = round(factor * dist[i - b] * 10000)
    #     if i >= firstProducer and i < firstProducer + numProducers:
    #         funds = max(funds, round(args.min_producer_funds * 10000))
    #     total += funds
    #     accounts[i]['funds'] = funds
    # return total
     for i in range(b, e):
        funds = 0
        if i == 0:
            funds = round(300000000.0000 * 10000) #3亿
        if i == 1:
            funds = round((700000000.0000 - (30 * 100000.0000 ))* 10000) #7亿 - 300万
        if i >= firstProducer and i < firstProducer + numProducers:
            funds = round(100000.0000 * 10000) #10万 
        a = accounts[i]        
        a['funds'] = funds
        print('#' * 80)
        print('# %d/%d %s %s' % (i, e, a['name'], intToCurrency(funds)))
        print('#' * 80)   

def createStakedAccounts(b, e):
    ramFunds = round(args.ram_funds * 10000)
    configuredMinStake = round(args.min_stake * 10000)
    maxUnstaked = round(args.max_unstaked * 10000)
    for i in range(b, e):
        a = accounts[i]
        funds = a['funds']
        print('#' * 80)
        print('# %d/%d %s %s' % (i, e, a['name'], intToCurrency(funds)))
        print('#' * 80)
        if funds < ramFunds:
            print('skipping %s: not enough funds to cover ram' % a['name'])
            continue
        minStake = min(funds - ramFunds, configuredMinStake)
        unstaked = min(funds - ramFunds - minStake, maxUnstaked)
        stake = funds - ramFunds - unstaked
        stakeNet = round(stake / 2)
        stakeCpu = stake - stakeNet
        if i == 1:
            stakeNet = ramFunds
            stakeCpu = ramFunds
            unstaked = funds - ramFunds - stakeNet - stakeCpu
        print('%s: total funds=%s, ram=%s, net=%s, cpu=%s, unstaked=%s' % (a['name'], intToCurrency(a['funds']), intToCurrency(ramFunds), intToCurrency(stakeNet), intToCurrency(stakeCpu), intToCurrency(unstaked)))
        assert(funds == ramFunds + stakeNet + stakeCpu + unstaked)
        retry(args.cleos + 'system newaccount --transfer vexcore %s %s --stake-net "%s" --stake-cpu "%s" --buy-ram "%s"   ' % 
            (a['name'], a['pub'], intToCurrency(stakeNet), intToCurrency(stakeCpu), intToCurrency(ramFunds)))
        if unstaked:
            retry(args.cleos + 'transfer vexcore %s "%s"' % (a['name'], intToCurrency(unstaked)))

def regProducers(b, e):
    for i in range(b, e):
        a = accounts[i]
        #retry(args.cleos + 'system regproducer ' + a['name'] + ' ' + a['pub'] + ' https://' + a['name'] + '.com' + '/' + a['pub'])
        retry(args.cleos + 'system regproducer ' + a['name'] + ' ' + a['pub'] + ' https://' + a['name'] + '.com' + '/')

def listProducers():
    run(args.cleos + 'system listproducers')

def vote(b, e):
    for i in range(b, e):
        voter = accounts[i]['name']
        if i == 1:
            continue
        k = args.num_producers_vote
        if k > numProducers:
            k = numProducers - 1
        prods = random.sample(range(firstProducer, firstProducer + numProducers), k)
        prods = ' '.join(map(lambda x: accounts[x]['name'], prods))
        retry(args.cleos + 'system voteproducer prods ' + voter + ' ' + prods)
        #sleep(1.0)

def claimRewards():
    table = getJsonOutput(args.cleos + 'get table vexcore vexcore producers -l 100')
    times = []
    for row in table['rows']:
        if row['unpaid_blocks'] and not row['last_claim_time']:
            times.append(getJsonOutput(args.cleos + 'system claimrewards -j ' + row['owner'])['processed']['elapsed'])
    print('Elapsed time for claimrewards:', times)

def proxyVotes(b, e):
    vote(firstProducer, firstProducer + 1)
    proxy = accounts[firstProducer]['name']
    retry(args.cleos + 'system regproxy ' + proxy)
    sleep(1.0)
    for i in range(b, e):
        voter = accounts[i]['name']
        retry(args.cleos + 'system voteproducer proxy ' + voter + ' ' + proxy)
        #sleep(1.0)

def updateAuth(account, permission, parent, controller):
    run(args.cleos + 'push action vexcore updateauth' + jsonArg({
        'account': account,
        'permission': permission,
        'parent': parent,
        'auth': {
            'threshold': 1, 'keys': [], 'waits': [],
            'accounts': [{
                'weight': 1,
                'permission': {'actor': controller, 'permission': 'active'}
            }]
        }
    }) + '-p ' + account + '@' + permission)

def resign(account, controller):
    updateAuth(account, 'owner', '', controller)
    updateAuth(account, 'active', 'owner', controller)
    sleep(1)
    run(args.cleos + 'get account ' + account)

def randomTransfer(b, e):
    for j in range(20):
        src = accounts[random.randint(b, e - 1)]['name']
        dest = src
        while dest == src:
            dest = accounts[random.randint(b, e - 1)]['name']
        run(args.cleos + 'transfer -f ' + src + ' ' + dest + ' "0.0001 ' + args.symbol + '"' + ' || true')

def msigProposeReplaceSystem(proposer, proposalName):
    requestedPermissions = []
    for i in range(firstProducer, firstProducer + numProducers):
        requestedPermissions.append({'actor': accounts[i]['name'], 'permission': 'active'})
    trxPermissions = [{'actor': 'vexcore', 'permission': 'active'}]
    with open(fastUnstakeSystem, mode='rb') as f:
        setcode = {'account': 'vexcore', 'vmtype': 0, 'vmversion': 0, 'code': f.read().hex()}
    run(args.cleos + 'multisig propose ' + proposalName + jsonArg(requestedPermissions) + 
        # jsonArg(trxPermissions) + 'set contract vexcore ' + args.contracts_dir + '/eosio.systemnew/' + ' -p ' + proposer)
        jsonArg(trxPermissions) + 'vexcore setcode' + jsonArg(setcode) + ' -p ' + proposer)
        # jsonArg(trxPermissions) + 'vexcore setcode ' + fastUnstakeSystem + ' -p ' + proposer)

def msigApproveReplaceSystem(proposer, proposalName):
    for i in range(firstProducer, firstProducer + numProducers):
        run(args.cleos + 'multisig approve ' + proposer + ' ' + proposalName +
            jsonArg({'actor': accounts[i]['name'], 'permission': 'active'}) +
            '-p ' + accounts[i]['name'])

def msigExecReplaceSystem(proposer, proposalName):
    retry(args.cleos + 'multisig exec ' + proposer + ' ' + proposalName + ' -p ' + proposer)

def msigReplaceSystem():
    # run(args.cleos + 'push action vex.token issue \'["vexcore", "10000000.0000 VEX", "memo"]\' -p vexcore' )
    # sleep(1)
    # #run(args.cleos + 'push action vexcore buyrambytes' + jsonArg(['vexcore', 'vexcore', 10000000]) + '-p vexcore')
    # # sleep(1)
    # run(args.cleos + 'push action vex.token transfer \'["vexcore","vexstake" "10000000.0000 VEX", "memo"]\' -p vexcore')
    # sleep(1)
    # run(args.cleos + 'push action vexcore buyrambytes' + jsonArg(['vexstake', accounts[0]['name'], 300000]) + '-p vexstake')
    # sleep(1)
    # # run(args.cleos + ' system delegatebw vexstake vexstake \"5000.0000 VEX\" \"5000.0000 VEX\" -p vexstake')
    # # sleep(1)
    # run(args.cleos + ' system delegatebw vexstake vexstake \"500.0000 VEX\" \"500000.0000 VEX\" -p vexstake')
    # sleep(1)
    msigProposeReplaceSystem(accounts[0]['name'], 'vote1bp')
    sleep(1)
    msigApproveReplaceSystem(accounts[0]['name'], 'vote1bp')
    msigExecReplaceSystem(accounts[0]['name'], 'vote1bp')

def produceNewAccounts():
    with open('newusers', 'w') as f:
        for i in range(120000, 200000):
            x = getOutput(args.cleos + 'create key --to-console')
            r = re.match('Private key: *([^ \n]*)\nPublic key: *([^ \n]*)', x, re.DOTALL | re.MULTILINE)
            name = 'user'
            for j in range(7, -1, -1):
                name += chr(ord('a') + ((i >> (j * 4)) & 15))
            print(i, name)
            f.write('        {"name":"%s", "pvt":"%s", "pub":"%s"},\n' % (name, r[1], r[2]))

def stepKillAll():
    run('killall keosd nodeos || true')
    sleep(2.5)
def stepStartWallet():
    startWallet()
    importKeys()
def stepStartBoot():
    startNode(0, {'name': 'vexcore', 'pvt': args.private_key, 'pub': args.public_key})
    sleep(5)
def stepInstallSystemContracts():
    run(args.cleos + 'set contract vex.token ' + args.contracts_dir + '/eosio.token/')
    run(args.cleos + 'set contract vex.msig ' + args.contracts_dir + '/eosio.msig/')
    sleep(5)
def stepCreateTokens():
    run(args.cleos + 'push action vex.token create \'["vexcore", "10000000000.0000 %s"]\' -p vex.token' % (args.symbol))
    run(args.cleos + 'push action vex.token issue \'["vexcore", "1000000000.0000 %s", "issue all to vexcore"]\' -p vexcore' % (args.symbol))
    allocateFunds(0, len(accounts))    
    # totalAllocation = allocateFunds(0, len(accounts))
    # run(args.cleos + 'push action vex.token issue \'["vexcore", "%s", "memo"]\' -p vexcore' % intToCurrency(totalAllocation))
    sleep(2)
def stepSetSystemContract():
    retry(args.cleos + 'set contract vexcore ' + args.contracts_dir + '/eosio.system/')
    sleep(2)
    run(args.cleos + 'push action vexcore setpriv' + jsonArg(['vex.msig', 1]) + '-p vexcore@active')
def stepInitSystemContract():
    run(args.cleos + 'push action vexcore init' + jsonArg(['0', '4,VEX']) + '-p vexcore@active')
    sleep(2)
def stepCreateStakedAccounts():
    createStakedAccounts(0, len(accounts))
def stepRegProducers():
    regProducers(firstProducer, firstProducer + numProducers)
    sleep(2)
    listProducers()
def stepStartProducers():
    startProducers(firstProducer, firstProducer + numProducers)
    sleep(args.producer_sync_delay)
def stepVote():
    vote(0, 0 + args.num_voters)
    sleep(2)
    listProducers()
    sleep(5)
def stepProxyVotes():
    proxyVotes(0, 0 + args.num_voters)
def stepResign():
    resign('vexcore', 'vex.prods')
    for a in systemAccounts:
        resign(a, 'vexcore')
def stepTransfer():
    while True:
        randomTransfer(0, args.num_senders)
def stepLog():
    run('tail -n 60 ' + args.nodes_dir + '00-vexcore/stderr')

# Command Line Arguments

parser = argparse.ArgumentParser()

commands = [
    ('k', 'kill',               stepKillAll,                True,    "Kill all nodeos and keosd processes"),
    ('w', 'wallet',             stepStartWallet,            True,    "Start keosd, create wallet, fill with keys"),
    ('b', 'boot',               stepStartBoot,              True,    "Start boot node"),
    ('s', 'sys',                createSystemAccounts,       True,    "Create system accounts (vex.*)"),
    ('c', 'contracts',          stepInstallSystemContracts, True,    "Install system contracts (token, msig)"),
    ('t', 'tokens',             stepCreateTokens,           True,    "Create tokens"),
    ('S', 'sys-contract',       stepSetSystemContract,      True,    "Set system contract"),
    ('I', 'init-sys-contract',  stepInitSystemContract,     True,    "Initialiaze system contract"),
    ('T', 'stake',              stepCreateStakedAccounts,   True,    "Create staked accounts"),
    ('p', 'reg-prod',           stepRegProducers,           True,    "Register producers"),
    ('P', 'start-prod',         stepStartProducers,         True,    "Start producers"),
    ('v', 'vote',               stepVote,                   True,    "Vote for producers"),
    ('R', 'claim',              claimRewards,               True,    "Claim rewards"),
    ('x', 'proxy',              stepProxyVotes,             False,   "Proxy votes"),
    ('q', 'resign',             stepResign,                 True,    "Resign vexcore"),
    ('m', 'msg-replace',        msigReplaceSystem,          False,   "Replace system contract using msig"),
    ('X', 'xfer',               stepTransfer,               False,   "Random transfer tokens (infinite loop)"),
    ('l', 'log',                stepLog,                    True,    "Show tail of node's log"),
]

parser.add_argument('--public-key', metavar='', help="VEXANIUM Public Key", default='VEX6LjFWJ6tfka3JAmsBttx1JdGznvkJ54h1oMWzAZEKnMUBWwv5Y', dest="public_key")
parser.add_argument('--private-Key', metavar='', help="VEXANIUM Private Key", default='5J4QZGBohrszShC2QEkhQXkiFG2oqRNd2XPUoGPDPS7qyXkX8hd', dest="private_key")
parser.add_argument('--cleos', metavar='', help="Cleos command", default='../../build/programs/cleos/cleos --wallet-url http://127.0.0.1:6666 ')
parser.add_argument('--nodeos', metavar='', help="Path to nodeos binary", default='../../build/programs/nodeos/nodeos')
parser.add_argument('--keosd', metavar='', help="Path to keosd binary", default='../../build/programs/keosd/keosd')
parser.add_argument('--contracts-dir', metavar='', help="Path to contracts directory", default='../../eosio.contracts/build/contracts')
parser.add_argument('--nodes-dir', metavar='', help="Path to nodes directory", default='./nodes/')
parser.add_argument('--genesis', metavar='', help="Path to genesis.json", default="./genesis.json")
parser.add_argument('--wallet-dir', metavar='', help="Path to wallet directory", default='./wallet/')
parser.add_argument('--log-path', metavar='', help="Path to log file", default='./output.log')
parser.add_argument('--symbol', metavar='', help="The vex.system symbol", default='VEX')
parser.add_argument('--user-limit', metavar='', help="Max number of users. (0 = no limit)", type=int, default=3000)
parser.add_argument('--max-user-keys', metavar='', help="Maximum user keys to import into wallet", type=int, default=10)
parser.add_argument('--ram-funds', metavar='', help="How much funds for each user to spend on ram", type=float, default=10.0)
parser.add_argument('--min-stake', metavar='', help="Minimum stake before allocating unstaked funds", type=float, default=10.0)
parser.add_argument('--max-unstaked', metavar='', help="Maximum unstaked funds", type=float, default=10)
parser.add_argument('--producer-limit', metavar='', help="Maximum number of producers. (0 = no limit)", type=int, default=0)
parser.add_argument('--min-producer-funds', metavar='', help="Minimum producer funds", type=float, default=1000.0000)
parser.add_argument('--num-producers-vote', metavar='', help="Number of producers for which each user votes", type=int, default=20)
parser.add_argument('--num-voters', metavar='', help="Number of voters", type=int, default=10)
parser.add_argument('--num-senders', metavar='', help="Number of users to transfer funds randomly", type=int, default=10)
parser.add_argument('--producer-sync-delay', metavar='', help="Time (s) to sleep to allow producers to sync", type=int, default=20)
parser.add_argument('-a', '--all', action='store_true', help="Do everything marked with (*)")
parser.add_argument('-H', '--http-port', type=int, default=8000, metavar='', help='HTTP port for cleos')

for (flag, command, function, inAll, help) in commands:
    prefix = ''
    if inAll: prefix += '*'
    if prefix: help = '(' + prefix + ') ' + help
    if flag:
        parser.add_argument('-' + flag, '--' + command, action='store_true', help=help, dest=command)
    else:
        parser.add_argument('--' + command, action='store_true', help=help, dest=command)
        
args = parser.parse_args()

args.cleos += '--url http://127.0.0.1:%d ' % args.http_port

logFile = open(args.log_path, 'a')

logFile.write('\n\n' + '*' * 80 + '\n\n\n')

with open('accounts.json') as f:
    a = json.load(f)
    if args.user_limit:
        del a['users'][args.user_limit:]
    if args.producer_limit:
        del a['producers'][args.producer_limit:]
    firstProducer = len(a['users'])
    numProducers = len(a['producers'])
    accounts = a['users'] + a['producers']#user 在前 bp在后
    bpaccounts = a['producers']

maxClients = numProducers + 10

haveCommand = False
for (flag, command, function, inAll, help) in commands:
    if getattr(args, command) or inAll and args.all:
        if function:
            haveCommand = True
            function()
if not haveCommand:
    print('bios-boot-tutorial.py: Tell me what to do. -a does almost everything. -h shows options.')
