function: FUN_140de3420
entry: 140de3420
body_size: 1134
signature: undefined FUN_140de3420()


void FUN_140de3420(longlong *param_1,undefined8 param_2,undefined8 *param_3,undefined8 param_4,
                  int *param_5,undefined8 param_6)

{
  int iVar1;
  undefined1 *puVar2;
  char cVar3;
  int iVar4;
  undefined1 auStack_88 [32];
  ulonglong local_68;
  undefined1 local_60;
  undefined1 *local_50;
  int *local_48;
  char local_3c [4];
  int local_38;
  int local_30;
  int local_28;
  int local_24;
  int local_20 [2];
  
  local_50 = auStack_88;
  iVar4 = 2;
  local_48 = local_20;
  do {
    *local_48 = 0;
    local_48 = local_48 + 1;
    iVar4 = iVar4 + -1;
  } while (iVar4 != 0);
  if (*param_5 == 0) {
    if (param_5[1] == 0) {
      local_68 = local_68 & 0xffffffff00000000;
      local_60 = 1;
      local_50 = auStack_88;
      FUN_140de3370(auStack_88,&DAT_140de38b4,1,0);
    }
    else {
      local_68 = CONCAT44(local_68._4_4_,param_5[1]);
      local_60 = 1;
      local_50 = auStack_88;
      FUN_140de3370(auStack_88,&DAT_140de38b6,1,1);
    }
  }
  else if (param_5[1] == 0) {
    local_68 = CONCAT44(local_68._4_4_,*param_5);
    local_60 = 1;
    local_50 = auStack_88;
    FUN_140de3370(auStack_88,&DAT_140de38b8,1,1);
  }
  else {
    puVar2 = auStack_88;
    if (*param_5 == param_5[1]) {
      iVar4 = (**(code **)(*param_1 + 0x18))(param_1);
      cVar3 = FUN_1400438c0(*param_3,param_3[1],(longlong)(*param_5 * iVar4));
      puVar2 = local_50;
      if (cVar3 != '\0') {
        local_68 = CONCAT44(local_68._4_4_,*param_5);
        local_60 = 1;
        FUN_140de3370(auStack_88,&LAB_140de38ba,1,0);
        return;
      }
    }
    local_50 = puVar2;
    (**(code **)*param_1)(param_1,param_2);
    local_68 = param_6;
    (**(code **)(*param_1 + 0x10))(param_1,param_3,param_4,param_5);
    local_24 = 0;
    iVar4 = (**(code **)(*param_1 + 0x28))();
    local_28 = 0;
    if (-1 < iVar4 + -1) {
      do {
        (**(code **)(*param_1 + 0x30))(param_1,local_3c,local_28);
        if (local_20[0] < local_38) {
          local_24 = local_24 + (local_38 - local_20[0]);
          local_20[0] = local_38;
        }
        local_24 = local_24 + local_30;
        if ((local_3c[0] == '\x02') && ((char)param_1[1] != '\0')) {
          local_24 = local_24 + local_30;
        }
        if (local_3c[0] != '\0') {
          local_20[0] = local_20[0] + local_30;
        }
        local_28 = local_28 + 1;
        iVar4 = iVar4 + -1;
      } while (iVar4 != 0);
    }
    if (local_20[0] < *param_5) {
      local_24 = local_24 + (*param_5 - local_20[0]);
    }
    local_20[0] = 0;
    (**(code **)(*param_1 + 0x20))(param_1,local_24);
    iVar4 = (**(code **)(*param_1 + 0x28))();
    local_28 = 0;
    if (-1 < iVar4 + -1) {
      do {
        (**(code **)(*param_1 + 0x30))(param_1,local_3c,local_28);
        if (local_20[0] < local_38) {
          local_68 = CONCAT44(local_68._4_4_,local_38 - local_20[0]);
          local_60 = 0;
          FUN_140de3370(auStack_88,&LAB_140de38ba,1,0);
        }
        iVar1 = local_30;
        if (local_3c[0] == '\0') {
          local_68 = CONCAT44(local_68._4_4_,local_30);
          local_60 = 0;
          FUN_140de3370(auStack_88,&DAT_140de38b6,1,1);
        }
        else if (local_3c[0] == '\x01') {
          local_68 = CONCAT44(local_68._4_4_,local_30);
          local_60 = 0;
          FUN_140de3370(auStack_88,&DAT_140de38b8,1,1);
        }
        else if ((char)param_1[1] == '\0') {
          local_68 = CONCAT44(local_68._4_4_,local_30);
          local_60 = 0;
          FUN_140de3370(auStack_88,&LAB_140de38ba,1,1);
        }
        else {
          local_60 = 0;
          FUN_140de3370(auStack_88,&DAT_140de38b8,1,1);
          local_68 = CONCAT44(local_68._4_4_,iVar1);
          local_60 = 0;
          FUN_140de3370(auStack_88,&DAT_140de38b6,1,1);
        }
        local_28 = local_28 + 1;
        iVar4 = iVar4 + -1;
      } while (iVar4 != 0);
    }
    if (local_20[0] < *param_5) {
      local_68 = CONCAT44(local_68._4_4_,*param_5 - local_20[0]);
      local_60 = 0;
      FUN_140de3370(auStack_88,&LAB_140de38ba,1,0);
    }
    (**(code **)(*param_1 + 8))(param_1);
  }
  return;
}


