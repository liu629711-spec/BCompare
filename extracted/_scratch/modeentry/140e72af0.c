function: FUN_140e72af0
entry: 140e72af0
body_size: 824
signature: undefined FUN_140e72af0()


void FUN_140e72af0(longlong param_1,byte param_2,int param_3)

{
  char cVar1;
  int iVar2;
  undefined4 uVar3;
  ulonglong uVar4;
  longlong lVar5;
  undefined1 auStack_a8 [40];
  undefined1 *local_80;
  int local_74;
  longlong local_70;
  longlong local_68;
  longlong local_60;
  longlong local_58;
  longlong local_50;
  longlong local_48;
  longlong local_40;
  char local_31;
  int local_30;
  int local_2c;
  
  local_80 = auStack_a8;
  local_40 = 0;
  local_30 = *(int *)(param_1 + 0x3c + (ulonglong)param_2 * 4) + 1;
  do {
    if (param_3 < local_30) {
code_r0x000140e72df7:
      *(int *)(param_1 + 0x3c + (ulonglong)param_2 * 4) = local_30 + -1;
      FUN_140013e30(&local_40);
      return;
    }
    (**(code **)(**(longlong **)(param_1 + 0x10) + 0x50))(*(longlong **)(param_1 + 0x10));
    cVar1 = (**(code **)(**(longlong **)(param_1 + 0x10) + 0x18))
                      (*(longlong **)(param_1 + 0x10),param_2,local_30);
    if (cVar1 == '\0') {
      *(int *)(param_1 + 0x20 + (ulonglong)param_2 * 4) = local_30 + -1;
      FUN_140e72e30(0,local_80);
      goto code_r0x000140e72df7;
    }
    uVar4 = (ulonglong)param_2;
    local_2c = local_30 - *(int *)(param_1 + 0x18 + uVar4 * 4);
    local_48 = *(longlong *)(param_1 + 0x60 + uVar4 * 8);
    local_50 = local_48;
    if (local_48 != 0) {
      local_50 = *(longlong *)(local_48 + -8);
    }
    lVar5 = (longlong)local_2c;
    if (lVar5 == local_50) {
      iVar2 = FUN_14052a190(local_2c,0x80);
      FUN_140019870(param_1 + 0x60 + uVar4 * 8,PTR_DAT_140006b80,1,(longlong)iVar2);
      local_58 = *(longlong *)(param_1 + 0x60 + uVar4 * 8);
      local_60 = local_58;
      if (local_58 != 0) {
        local_60 = *(longlong *)(local_58 + -8);
      }
      FUN_140019870(param_1 + 0x70 + uVar4 * 8,PTR_DAT_1400214c8,1,local_60);
      local_68 = *(longlong *)(param_1 + 0x60 + uVar4 * 8);
      local_70 = local_68;
      if (local_68 != 0) {
        local_70 = *(longlong *)(local_68 + -8);
      }
      FUN_140019870(param_1 + 0xb0 + uVar4 * 8,PTR_DAT_140006b80,1,local_70);
    }
    FUN_140e71db0(*(undefined8 *)(param_1 + 0x10),&local_40,param_2,local_30);
    local_31 = local_40 != 0;
    if (!(bool)local_31) {
      (**(code **)(**(longlong **)(param_1 + 0x10) + 0x40))
                (*(longlong **)(param_1 + 0x10),&local_40,param_2,local_30);
    }
    local_74 = 0;
    if (local_40 != 0) {
      local_74 = *(int *)(local_40 + -4);
    }
    uVar3 = FUN_1405efdc0(0xffffffff,local_40,local_74 * 2);
    *(undefined4 *)(*(longlong *)(param_1 + 0x60 + uVar4 * 8) + lVar5 * 4) = uVar3;
    *(char *)(*(longlong *)(param_1 + 0x70 + uVar4 * 8) + lVar5) = local_31;
    if (local_31 != '\0') {
      (**(code **)(**(longlong **)(param_1 + 0x10) + 0x40))
                (*(longlong **)(param_1 + 0x10),&local_40,param_2,local_30);
    }
    uVar3 = (**(code **)(**(longlong **)(param_1 + 0x10) + 0x60))
                      (*(longlong **)(param_1 + 0x10),param_2,local_40);
    uVar3 = FUN_140e75c50(local_40 == 0,local_31,uVar3);
    *(undefined4 *)(*(longlong *)(param_1 + 0xb0 + uVar4 * 8) + lVar5 * 4) = uVar3;
    local_30 = local_30 + 1;
    (**(code **)(**(longlong **)(param_1 + 0x10) + 0x58))(*(longlong **)(param_1 + 0x10));
  } while( true );
}


