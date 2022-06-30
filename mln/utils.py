from ast import literal_eval
from django.contrib.auth.models import User
from mln.models import Referral
from rest_framework.response import Response
from django.db.models import F


def sp_user_levels(**kwargs):
    ss_data = ss_user_levels(ss_id=kwargs['ss_id'],
                             level_0=kwargs['level_0'], level_1=kwargs['level_1'], level_2=kwargs['level_2'],
                              level_3=kwargs['level_3'], level_4=kwargs['level_4'])
    if Referral.objects.filter(user_id=kwargs['sp_id']).exists():
        obj = Referral.objects.filter(user_id=kwargs['sp_id']).first()
        parents = obj.tn_ancestors_pks
        level = obj.tn_level
        incentives = incentive_distribution(user_id=kwargs['sp_id'],
                                            level_0=kwargs['level_0'], level_1=kwargs['level_1'],
                                            level_2=kwargs['level_2'],
                                            level_3=kwargs['level_3'], level_4=kwargs['level_4'])
        admin_user = User.objects.filter(id=kwargs['admin_id']).values('id', 'is_superuser', name=F('first_name'))
        admin_user_list = []
        for x in admin_user:
            x.update({"level": 0, "incentives": incentives[0] + incentives[0]})
            admin_user_list.append(x)

        if level < 6:
            if level == 1:
                data = "No parent available"
                return data, ss_data, admin_user_list
            if level == 2:
                parents = obj.tn_ancestors_pks
                parent_users = Referral.objects.filter(id=parents, is_deleted=False)

                data = parent_users.values('id', 'tn_parent_id', provider_id=F('user__id'), name=F('user__first_name'))
                data_list = []
                i = 0
                for x in data:
                    i = i + 1
                    x.update({"level": i, "incentives": incentives[i]})
                    data_list.append(x)
                return data_list, ss_data, admin_user_list
            parents = obj.tn_ancestors_pks
            parents_last = literal_eval(parents)
            parent_users = Referral.objects.filter(id__in=parents_last, is_deleted=False)

            data = parent_users.values('id', 'tn_parent_id', provider_id=F('user__id'), name=F('user__first_name'))
            data_list = []
            i = 0
            for x in data:
                i = i + 1
                x.update({"level": i, "incentives": incentives[i]})
                data_list.append(x)
            return data_list, ss_data, admin_user_list
        else:
            level = obj.tn_level - 4
            level_first_user = Referral.all_objects.get(tn_level=level, tn_descendants_pks__contains=obj.id)
            level_first_parents = level_first_user.tn_ancestors_pks
            parents_first = literal_eval(level_first_parents)
            parents_last = literal_eval(parents)
            if type(parents_first) == int:
                level_first_parents_list = tuple(int(el) for el in level_first_parents.split(' '))
                required_parents_list = list(set(parents_last) ^ set(level_first_parents_list))

                parent_users = Referral.objects.filter(id__in=required_parents_list, is_deleted=False)

                data = parent_users.values('id', 'tn_parent_id', provider_id=F('user__id'), name=F('user__first_name'))
                data_list = []
                i = 0
                for x in data:
                    i = i + 1
                    x.update({"level": i, "incentives": incentives[i]})
                    data_list.append(x)
                return data_list, ss_data, admin_user_list
            required_parents = list(set(parents_last) ^ set(parents_first))
            parent_users = Referral.objects.filter(id__in=required_parents, is_deleted=False)

            data = parent_users.values('id', 'tn_parent_id', provider_id=F('user__id'), name=F('user__first_name'))
            data_list = []
            i = 0
            for x in data:
                i = i + 1
                x.update({"level": i, "incentives": incentives[i]})
                data_list.append(x)
            return data_list, ss_data, admin_user_list

    else:
        return False


def ss_user_levels(**kwargs):
    if Referral.objects.filter(user_id=kwargs['ss_id']).exists():
        obj = Referral.objects.get(user_id=kwargs['ss_id'])
        parents = obj.tn_ancestors_pks
        level = obj.tn_level

        incentives = incentive_distribution(user_id=kwargs['ss_id'],
                               level_0=kwargs['level_0'], level_1=kwargs['level_1'], level_2=kwargs['level_2'],
                               level_3=kwargs['level_3'], level_4=kwargs['level_4'])
        if level < 6:
            if level == 1:
                data = "No parent available"
                return data
            if level == 2:
                parents = obj.tn_ancestors_pks
                parent_users = Referral.objects.filter(id=parents, is_deleted=False)

                data = parent_users.values('id', 'tn_parent_id', seeker_id=F('user__id'), name=F('user__first_name'))
                data_list = []
                i = 0
                for x in data:
                    i = i + 1
                    x.update({"level": i, "incentives": incentives[i]})
                    data_list.append(x)
                return data_list
            parents = obj.tn_ancestors_pks
            parents_last = literal_eval(parents)
            parent_users = Referral.objects.filter(id__in=parents_last, is_deleted=False)

            data = parent_users.values('id', 'tn_parent_id', seeker_id=F('user__id'), name=F('user__first_name'))
            data_list = []
            i = 0
            for x in data:
                i = i + 1
                x.update({"level": i, "incentives": incentives[i]})
                data_list.append(x)
            return data_list
        else:
            level = obj.tn_level - 4
            level_first_user = Referral.all_objects.get(tn_level=level, tn_descendants_pks__contains=obj.id)
            level_first_parents = level_first_user.tn_ancestors_pks
            parents_first = literal_eval(level_first_parents)
            parents_last = literal_eval(parents)
            if type(parents_first) == int:
                level_first_parents_list = tuple(int(el) for el in level_first_parents.split(' '))
                required_parents_list = list(set(parents_last) ^ set(level_first_parents_list))

                parent_users = Referral.objects.filter(id__in=required_parents_list, is_deleted=False)

                data = parent_users.values('id', 'tn_parent_id', seeker_id=F('user__id'), name=F('user__first_name'))
                data_list = []
                i = 0
                for x in data:
                    i = i + 1
                    x.update({"level": i, "incentives": incentives[i]})
                    data_list.append(x)
                return data_list
            required_parents = list(set(parents_last) ^ set(parents_first))
            parent_users = Referral.objects.filter(id__in=required_parents, is_deleted=False)

            data = parent_users.values('id', 'tn_parent_id', seeker_id=F('user__id'), name=F('user__first_name'))
            data_list = []
            i = 0
            for x in data:
                i = i + 1
                x.update({"level": i, "incentives": incentives[i]})
                data_list.append(x)
            return data_list

    else:
        return False


def incentive_distribution(**kwargs):
    if Referral.objects.filter(user_id=kwargs['user_id']).exists():
        obj = Referral.objects.get(user_id=kwargs['user_id'])
        #
        # sp_amount = (kwargs['amount'] * kwargs['sp_amount']) / 100
        # company = (kwargs['amount'] * kwargs['company']) / 100
        # convenience_fee = (kwargs['amount'] * kwargs['convenience_fee']) / 100
        # # convenience_fee = kwargs['convenience_fee'] / 100
        # total_company_fee = company + convenience_fee
        # admin_set_amount = (total_company_fee * 20) / 100
        # amount_levels = admin_set_amount / 2

        level_0_amount = kwargs['level_0']
        level_1_amount = kwargs['level_1']
        level_2_amount = kwargs['level_2']
        level_3_amount = kwargs['level_3']
        level_4_amount = kwargs['level_4']

        return level_0_amount, level_1_amount, level_2_amount, level_3_amount, level_4_amount

    else:
        return False


def referral_soft_delete(**kwargs):
    if Referral.all_objects.filter(id=kwargs['id']).exists():
        Referral.all_objects.filter(id=kwargs['id']).delete()
        return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
    else:
        return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})


def restore_referral_from_softdelete(**kwargs):
    if Referral.all_objects.filter(id=kwargs['id']).exists():
        Referral.all_objects.filter(id=kwargs['id']).restore()
        return Response({"status": True, "message": "{} Restore Successfully!".format(kwargs['msg'])})
    else:
        return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})


def check_reference_id(**kwargs):
    try:
        if kwargs['User'].objects.filter(profile__reference_id=kwargs['reference_id']).exists():
            parent_user = kwargs['User'].objects.get(profile__reference_id=kwargs['reference_id'])
            if Referral.objects.filter(user=parent_user).exists():
                ref_parent_user = Referral.objects.get(user=parent_user)
                Referral.objects.create(user=kwargs['user'], tn_parent=ref_parent_user)
                return True
            else:
                new_parent_user = Referral.objects.create(user=parent_user)
                Referral.objects.create(user=kwargs['user'], tn_parent=new_parent_user)
                return True
        else:
            return False
    except:
        return False


def referral_permanent_delete(**kwargs):
    if Referral.all_objects.filter(id=kwargs['id']).exists():
        Referral.all_objects.filter(id=kwargs['id']).hard_delete()
        return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
    else:
        return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})

