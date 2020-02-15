# -*- coding:gbk -*-

import os
import logging
import utils.log
import re
import random
import handler.game_rec as rec
import json
import handler.lottery as lottery


logger = logging.getLogger(utils.log.Logger.LOGGER_NAME)


def roll_dice(express):
    index_d = express.find('d')
    if index_d == -1:
        index_d = express.find('D')
    if index_d == -1:
        return ['�̶�{}'.format(express), int(express)]
    num_of_dice = 1
    if index_d != 0:
        num_of_dice = int(express[0:index_d])
    max_value_of_dice = int(express[index_d + 1:])
    array = []
    val = 0
    for i in range(num_of_dice):
        res = random.randint(1, max_value_of_dice)
        array.append(str(res))
        val = val + res
    result = ['[' + ','.join(array) + ']', val]
    return result


def covert_at(at_str):
    match = re.findall(r'\d{6,}', at_str)
    if len(match) > 0:
        return match[0]
    return ""


def check(player, item):
    if player.getSkill(item) < 0:
        res = player.getSkill(item)
        if res < 0:
            res = player.getSkill(item)
        return res
    else:
        return player.getSkill(item)


def touch(player, item):
    if player.getSkill(item) < 0:
        key = item
        res = player.getSkill(key)
        if res < 0:
            logger.info(2)
            key = item
            res = player.getSkill(key)
            if res < 0:
                return False
        return key
    else:
        return item


class CommandDispatcher(object):
    def __init__(self):
        random.seed()
        logger.info('dispatcher inited')
        self.games = {}
        self.cmd_dict = {'r': RollDiceCommand(), 'coc7': RoleGenerateCommand(), 'c': CheckCommand(self.games),
                         'sc': SanCheckCommand(self.games), 'join': JoinCommand(self.games),
                         'startGame': StartGameCommand(self.games), 'exitGame': ExitGameCommand(self.games),
                         'v': ViewCommand(self.games), 'save': SaveGameCommand(self.games),
                         'load': LoadGameCommand(self.games), 'd': DamageCommand(self.games),
                         'luck': LuckCommand(), 'ping': PingCommand()}

        self.cmd_dict['help'] = HelpCommand(self.cmd_dict)

    def __del__(self):
        logger.info('dispatcher del')

    @staticmethod
    def is_command(msg):
        if type(msg) != str:
            return False
        if msg[0] == "/":
            return True
        return False

    def execute_cmd(self, msg, from_qq, from_group):
        end_cmd = msg.find(" ")
        if end_cmd == -1:
            end_cmd = len(msg)
        cmd = msg[1:end_cmd]
        try:
            handler = self.cmd_dict[cmd]
        except KeyError:
            return "������ڣ���ʹ��/help�鿴����֧�ֵ�ָ��"
        msg = re.sub(r'\s+', ' ', msg)
        args = msg.split(' ')[1:]
        # for i in range(len(args)):
        #    args[i] = args[i].decode('gbk')

        logger.info('entered{3},{0},{1},{2}'.format(args, from_qq, from_group, cmd))
        return handler.execute_cmd(args, str(from_qq), str(from_group))


class AbstractCommand(object):
    def execute_cmd(self, args, from_qq, from_group):
        raise NotImplementedError('abstract')

    def help(self):
        raise NotImplementedError('abstract')


class RollDiceCommand(AbstractCommand):
    def execute_cmd(self, args, from_qq, from_group):
        logger.info("�������������args:" + str(args))
        is_private = False
        result = "��ʽ����"
        if len(args) == 0:
            result = '�������: ' + roll_dice('1D100')[0]
            return result
        for arg in args:
            if re.match('^h$', arg):
                is_private = True
                continue

            if re.search(r'\d*[dD]\d+', arg):
                match_arr = re.findall(r'\d*[dD]\d+', arg)
                dice_arr = []
                for express in match_arr:
                    dice = roll_dice(express)
                    dice_arr.append(dice[0])
                    arg = arg.replace(express, str(dice[1]))

                if len(dice_arr) > 1:
                    result = '�������: ' + arg
                else:
                    result = '�������: ' + dice_arr[0]

                result = result + ' , ����:' + str(eval(arg))
        return [result, is_private, '���������˽�ķ���']

    def help(self):
        return '/r[h] ���ӱ��ʽ\n  - �������� [����n]d[����m] ����ΪͶ��n��m������\n  - hΪ����'


class RoleGenerateCommand(AbstractCommand):
    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("�����������Ա��������")
        if len(args) == 0:
            num = 1
        else:
            num = int(args[0])
            num = num if num <= 5 else 5

        status = {'����': True, '����': True, '����': False, '����': True, '��ò': True, '����': False, '��־': True, '����': True}
        result = "��������������£�\n"
        array = []
        for i in range(num):
            array = []
            for key, value in status.items():
                if value:
                    dice = roll_dice('3d6')[1]
                else:
                    dice = (roll_dice('2d6')[1] + 6)
                array.append(key + ": " + str(dice * 5))
            result += ", ".join(array) + "\n"

        return result

    def help(self):
        return '/coc7 [����] �������Ա����'


class CheckCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("����춨����")

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        if len(args) == 0:
            return '������Ҫ�춨�����Ի���'
        player = fromQQ
        logger.info(type(fromQQ))
        index = 0
        call = "��"
        if len(args) > 1:
            call = args[0]
            player = covert_at(args[0])
            index = 1

        player = self.gamesDict[from_group].getRole(player)
        if not player:
            return call + "û�вμ���Ϸ"

        needBelow = check(player, args[index])
        if not needBelow:
            return call + "û�и����Ի��ܡ�"

        result = ""
        dice = random.randint(1, 100)
        if dice > needBelow:
            result = "ʧ��"
        else:
            result = "�ɹ�"
        if dice < needBelow / 2:
            result = "���ѳɹ�"
        if dice < needBelow / 5:
            result = "���ѳɹ�"
        if (needBelow > 50 and dice == 100) or (needBelow <= 50 and dice >= 96):
            result = "��ʧ��"
        elif dice == 1:
            result = "��ɹ�"

        result = "{4}��{0}Ϊ{1}, Ͷ�����Ϊ{2}, �춨�����{3}��".format(args[index], needBelow, dice, result, call)
        return result

    def help(self):
        return '/c [at��Ҫ�춨�����] ��Ҫ�춨������'


class SanCheckCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("����sancheck�춨����")

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        if len(args) == 0:
            return '������sc���ʽ'
        player = fromQQ
        index = 0
        call = "��"
        if len(args) > 1:
            call = args[0]
            player = covert_at(args[0])
            index = 1

        player = self.gamesDict[from_group].getRole(player)
        if not player:
            return call + "û�вμ���Ϸ"

        needBelow = check(player, 'san')
        if not needBelow:
            return call + "û�и����Ի��ܡ�"

        result = True
        dice = random.randint(1, 100)
        if dice > needBelow:
            result = False

        slashIndex = args[index].find('/')

        damage = args[index][0:slashIndex] if result else args[index][slashIndex + 1:]
        result = "�ɹ�" if result else "ʧ��"
        diceValue = roll_dice(damage)
        trueDamage = diceValue[1]
        player.setSkill('san', needBelow - trueDamage)

        result = "{4}��{0}��ǰΪ{1}, Ͷ�����Ϊ{2}, �춨�����{3}���۳�sanֵ{5}�㣬��ǰsanֵ��{6}".format('sanֵ', needBelow, dice, result, call,
                                                                                  trueDamage, needBelow - trueDamage)
        return result

    def help(self):
        return '/sc [at��Ҫ�춨�����] [sc���ʽ]'


class StartGameCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("QȺ" + str(from_group) + "ʹ�ÿ�����Ϸ����")

        if from_group in self.gamesDict:
            return "��Ⱥ�Ѿ��п�ʼ����Ϸ�����������¿�ʼ��ʹ��/exitGame�������˳���"

        self.gamesDict[from_group] = rec.Game()
        return "��Ϸ��ʼ����"

    def help(self):
        return '/startGame ����һ����Ϸ'


class ExitGameCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("QȺ" + str(from_group) + "ʹ�ý�����Ϸ����")

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        self.gamesDict.pop(from_group)
        return "��Ϸ���˳���"

    def help(self):
        return '/exitGame �ر����ڽ��е���Ϸ'


class SaveGameCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("QȺ" + str(from_group) + "ʹ�ô�����Ϸ����")

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        name = str(from_group)
        if len(args) != 0:
            name = args[0]

        self.gamesDict[from_group].saveGame(name)
        return "��Ϸ�Ѵ��档"

    def help(self):
        return '/save [�浵����Ĭ��ΪqqȺ��] �浵���ڽ��е���Ϸ'


class LoadGameCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("QȺ" + str(from_group) + "ʹ�ö�ȡ��Ϸ����")

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        name = str(from_group)
        if len(args) != 0:
            name = args[0]

        self.gamesDict[from_group].loadGame(name)
        return "��Ϸ�Ѷ�ȡ��ϡ�"

    def help(self):
        return '/load [�浵����Ĭ��ΪqqȺ��] ��ȡ�浵'


class JoinCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("QȺ{0}�û�{1}ʹ�òμ���Ϸ����".format(from_group, fromQQ))

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        player = fromQQ
        roleStr = ""
        if args[0].find("CQ:at") != -1:
            player = covert_at(args[0])
            roleStr = " ".join(args[1:])
            logger.info(roleStr)
        else:
            roleStr = " ".join(args)
        self.gamesDict[from_group].addRole(player, roleStr)
        skills = self.gamesDict[from_group].getRole(player).getAll()
        arr = []
        for key, value in skills.items():
            arr.append("{0}: {1}".format(key, value))

        return "[CQ:at,qq={0}]�ѳɹ��μ���Ϸ����˶��������ԣ�\n".format(player) + ", ".join(arr)

    def help(self):
        return '/join [������������Ϣ] ���뱾Ⱥ���е���Ϸ'


class ViewCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):

        if from_group not in self.gamesDict:
            return "��Ⱥû�����ڽ��е���Ϸ��"

        if len(args) == 0:
            return "������Ҫ�鿴�ļ��ܻ�����"

        if len(args) == 1:
            player = self.gamesDict[from_group].getRole(fromQQ)
            if not player:
                return "��û�вμ���Ϸ"
            if args[0] != 'all':
                return "�������ԣ�" + args[0] + "Ϊ" + str(check(player, args[0]))
            elif args[0] == 'all':
                skills = player.getAll()
                arr = []
                for key, value in skills.items():
                    arr.append("{0}: {1}".format(key, value))
                return "�������ԣ�\n" + ", ".join(arr)

        if len(args) == 2:
            args[0] = covert_at(args[0])
            player = self.gamesDict[from_group].getRole(args[0])
            if not player:
                return "�����û�вμ���Ϸ"

            if args[1] != 'all':
                return "[CQ:at,qq={0}]�����ԣ�{1} Ϊ {2}".format(args[0], args[1], str(check(player, args[1])))
            elif args[1] == 'all':
                skills = player.getAll()
                arr = []
                for key, value in skills.items():
                    arr.append("{0}: {1}".format(key, value))
                return "[CQ:at,qq={0}]".format(args[0]) + "�����ԣ�\n" + ", ".join(arr)

    def help(self):
        return '/v [atҪ�鿴����ң������ǲ鿴�Լ�] ���Ի��� �鿴��ҵ�״̬'


class DamageCommand(AbstractCommand):
    def __init__(self, gamesDict):
        self.gamesDict = gamesDict

    def execute_cmd(self, args, fromQQ, from_group):
        if from_group not in self.gamesDict:
            return '��Ⱥû���Ѿ���ʼ����Ϸ��'
        if len(args) < 2:
            return '���������[����][�˺����ʽ]'
        player = fromQQ
        call = '��'
        if len(args) == 3:
            call = args[0]
            player = covert_at(args[0])
            args.pop(0)

        player = self.gamesDict[from_group].getRole(player)
        if not player:
            return call + "û������Ϸ��"

        key = touch(player, args[0])
        if not key:
            return call + "û�и�����"

        nowVal = player.getSkill(key)
        matchArr = re.findall('\d*[dD]\d+', args[1])
        diceArr = []
        for express in matchArr:
            dice = roll_dice(express)
            diceArr.append(dice[0])
            args[1] = args[1].replace(express, str(dice[1]))
        damage = eval(args[1])
        text = "��ʧ"
        if damage < 0:
            text = "�ָ�"
        player.setSkill(key, nowVal - damage)
        nowVal = player.getSkill(key)
        return "{0}{1}��{2}��{3}, ��ǰֵΪ{4}".format(call, text, abs(damage), args[0], nowVal)

    def help(self):
        return '/d [at���] ���� �˺����ʽ  ָ��ĳ�����ܵ����ٵ��˺���ָ�'


class HelpCommand(AbstractCommand):
    def __init__(self, cmdDict):
        self.cmdDict = cmdDict

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("�����������")
        result = ""
        for cmd, obj in self.cmdDict.items():
            result += obj.help() + "\n"

        return result

    def help(self):
        return '/help �鿴�������'


class LuckCommand(AbstractCommand):
    def __init__(self):
        self.lottery = lottery.Lottery()

    def execute_cmd(self, args, fromQQ, from_group):
        logger.info("����luck����")
        result = self.lottery.draw()

        return result

    def help(self):
        return '/luck ��ǩ'


class PingCommand(AbstractCommand):
    def __init__(self):
        pass

    def execute_cmd(self, args, fromQQ, from_group):
        return "ping��ping��ping��ping��ping��\nping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��" \
               "ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��ping��" \
               "/ping/ping/ping/ping/ping/ping/ping/ping/ping/ping/ping/ping/ping/ping/ping"

    def help(self):
        return '/ping �����ǲ��ǻ���'
