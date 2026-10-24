function: FUN_141025e10
entry: 141025e10
body_size: 2348
signature: undefined FUN_141025e10()


void FUN_141025e10(longlong param_1,undefined1 param_2,int *param_3,longlong param_4,int *param_5)

{
  char cVar1;
  undefined1 uVar2;
  int iVar3;
  int iVar4;
  undefined8 uVar5;
  undefined8 uVar6;
  undefined1 auStack_f8 [32];
  undefined8 local_d8;
  longlong local_d0;
  longlong local_c0;
  longlong local_b8;
  undefined1 *local_b0;
  int local_9c;
  longlong local_98;
  bool local_8f;
  ushort local_8e;
  int local_8c;
  int local_88;
  int local_84;
  int local_80;
  int local_7c;
  longlong local_78;
  longlong local_70;
  longlong local_68;
  longlong local_60;
  int local_54;
  int local_50;
  int local_4c;
  int local_48;
  char local_42;
  char local_41;
  int local_40;
  int local_3c;
  int local_38;
  int local_34;
  undefined1 local_30 [24];
  
  local_b0 = auStack_f8;
  local_c0 = 0;
  local_b8 = 0;
  local_60 = 0;
  local_68 = 0;
  FUN_140016d40(local_30,PTR_DAT_1405f0778);
  local_54 = *(int *)(param_1 + 0x30);
  do {
    local_54 = local_54 + -1;
    if (local_54 < 0) {
      FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x4c3);
    }
    iVar3 = FUN_141028b00(param_1,param_2,local_54);
    local_4c = iVar3;
  } while (iVar3 < 0);
  uVar5 = FUN_141028aa0(param_1,param_2);
  uVar5 = FUN_141015bf0(uVar5);
  iVar4 = FUN_140672920(uVar5);
  if (iVar3 != iVar4 + -1) {
    FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x4c6);
  }
  local_41 = '\0';
  uVar5 = FUN_141028aa0(param_1,param_2);
  uVar5 = FUN_141015bf0(uVar5);
  FUN_141011830(uVar5,&local_60,param_4);
  local_70 = local_60;
  if (local_60 != 0) {
    local_70 = *(longlong *)(local_60 + -8);
  }
  local_40 = (int)local_70 + -1;
  iVar3 = *param_3;
  if (iVar3 < local_54) {
    local_4c = FUN_141028b00(param_1,param_2,iVar3);
    if (local_4c < 0) {
      if (param_3[1] != 1) {
        FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x4df
                     );
      }
      local_3c = *param_3;
      do {
        local_4c = -1;
        local_3c = local_3c + -1;
        if (local_3c < 0) break;
        local_4c = FUN_141028b00(param_1,param_2,local_3c);
      } while (local_4c < 0);
      local_4c = local_4c + 1;
      uVar5 = FUN_141028aa0(param_1,param_2);
      uVar5 = FUN_141015bf0(uVar5);
      uVar5 = FUN_140672d20(uVar5,local_4c);
      cVar1 = FUN_14051f210(uVar5);
      if (cVar1 != '\0') {
        FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x4e9
                     );
      }
      if (param_4 == 0) {
        local_8f = true;
      }
      else {
        local_8c = 0;
        if (param_4 != 0) {
          local_8c = *(int *)(param_4 + -4);
        }
        local_8e = *(ushort *)(param_4 + -2 + (longlong)local_8c * 2);
        if (local_8e < 0x100) {
          local_8f = ((byte)(&DAT_141026872)[(longlong)(ulonglong)local_8e >> 3] >>
                      ((ulonglong)local_8e & 7) & 1) != 0;
        }
        else {
          local_8f = false;
        }
        local_8f = !local_8f;
      }
      if (local_8f != false) {
        local_41 = '\x01';
        uVar5 = FUN_141028aa0(param_1,param_2);
        uVar5 = FUN_141015bf0(uVar5);
        uVar2 = FUN_140672c30(uVar5);
        *(undefined1 *)(local_60 + 8 + (longlong)local_40 * 0x10) = uVar2;
        iVar3 = local_40 + 2;
        local_40 = local_40 + 1;
        FUN_140019870(&local_60,PTR_DAT_14051d728,1,(longlong)iVar3);
        FUN_14051f090(local_60 + (longlong)local_40 * 0x10,0,0);
      }
    }
    goto LAB_141026385;
  }
  if (local_54 < iVar3) {
    if (param_3[1] != 1) {
      FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x4cc);
    }
    uVar5 = FUN_141028aa0(param_1,param_2);
    uVar5 = FUN_141015bf0(uVar5);
    FUN_141012bd0(uVar5,&local_b8,local_4c);
    local_78 = local_b8;
    local_7c = 0;
    if (local_b8 != 0) {
      local_7c = *(int *)(local_b8 + -4);
    }
    local_50 = local_7c + 1;
    if (1 < local_50) {
      local_d8 = 0;
      FUN_141025e10(param_1,param_2,&local_54,&DAT_14102686c);
      local_54 = local_54 + 1;
    }
  }
  local_4c = FUN_141028b00(param_1,param_2,local_54);
  if (local_40 < 1) {
LAB_141026103:
    if (local_54 < *param_3) {
      local_88 = *param_3;
    }
    else {
      local_88 = local_54;
    }
    local_38 = local_88;
  }
  else {
    uVar5 = FUN_141028aa0(param_1,param_2);
    uVar5 = FUN_141015bf0(uVar5);
    cVar1 = FUN_140672c80(uVar5);
    if (cVar1 == '\0') goto LAB_141026103;
    local_80 = *(int *)(param_1 + 0x30) + -1;
    local_84 = local_80;
    if (*param_3 + local_40 < local_80) {
      local_84 = *param_3 + local_40;
    }
    local_38 = local_84;
  }
  if (local_54 < local_38) {
    uVar5 = FUN_141028b70(param_1);
    local_d8 = CONCAT71(local_d8._1_7_,param_2);
    local_d0 = CONCAT44(local_d0._4_4_,local_38);
    uVar6 = FUN_14102caf0(PTR_PTR_141021f78,1,param_1,local_54);
    FUN_1405f1830(uVar5,uVar6,1);
  }
LAB_141026385:
  local_38 = *param_3;
  local_48 = param_3[1];
  local_42 = '\x01';
  if (0 < local_40) {
    FUN_140019870(&local_68,PTR_DAT_14101e270,1,(longlong)local_40);
    local_34 = local_4c;
    if (1 < param_3[1]) {
      local_38 = local_38 + 1;
      local_34 = local_4c + 1;
    }
    local_3c = 0;
    while (((local_3c < local_40 && (local_38 + local_3c < *(int *)(param_1 + 0x30))) &&
           (iVar3 = FUN_141028b00(param_1,param_2,local_38 + local_3c), iVar3 < 0))) {
      *(int *)(local_68 + (longlong)local_3c * 8) = local_34 + local_3c;
      *(undefined1 *)(local_68 + 4 + (longlong)local_3c * 8) = 2;
      local_3c = local_3c + 1;
    }
    for (; local_3c < local_40; local_3c = local_3c + 1) {
      *(int *)(local_68 + (longlong)local_3c * 8) = local_34 + local_3c;
      *(undefined1 *)(local_68 + 4 + (longlong)local_3c * 8) = 0;
    }
    if ((param_3[1] < 2) && (*(longlong *)(local_60 + (longlong)local_40 * 0x10) == 0)) {
      local_42 = '\0';
    }
    else {
      local_42 = '\x01';
    }
  }
  FUN_1405f1710(local_30);
  uVar5 = FUN_141028aa0(param_1,param_2);
  uVar5 = FUN_141015bf0(uVar5);
  uVar5 = FUN_141010820(uVar5,&local_4c,local_60);
  FUN_1405f1730(local_30,uVar5,1);
  if (local_42 != '\0') {
    uVar5 = FUN_14102c500(PTR_PTR_141022328,1,param_1,*param_3);
    FUN_1405f16b0(local_30,uVar5);
  }
  if (0 < local_40) {
    local_d8 = CONCAT71(local_d8._1_7_,param_2);
    local_d0 = local_68;
    uVar5 = FUN_14102c860(PTR_PTR_141021c08,1,param_1,local_38);
    FUN_1405f16b0(local_30,uVar5);
  }
  uVar5 = FUN_141028b70(param_1);
  FUN_1405f1940(uVar5,local_30);
  if (0 < local_40) {
    FUN_141026eb0(param_1);
  }
  FUN_1410270c0(param_1);
  if (param_5 != (int *)0x0) {
    uVar5 = FUN_141028aa0(param_1,param_2);
    uVar5 = FUN_141015bf0(uVar5);
    FUN_1410108c0(uVar5,&local_4c,local_60);
    param_5[1] = local_48;
    if ((0 < local_40) && (*param_5 = *param_5 + local_40, local_41 != '\0')) {
      *param_5 = *param_5 + -1;
      uVar5 = FUN_141028aa0(param_1,param_2);
      uVar5 = FUN_141015bf0(uVar5);
      FUN_141012bd0(uVar5,&local_c0,local_4c + -1);
      local_98 = local_c0;
      local_9c = 0;
      if (local_c0 != 0) {
        local_9c = *(int *)(local_c0 + -4);
      }
      param_5[1] = local_9c + 1;
    }
  }
  FUN_140013f10(&local_c0,2);
  FUN_140019a50(&local_68,PTR_DAT_14101e270);
  FUN_140019a50(&local_60,PTR_DAT_14051d728);
  FUN_140017370(local_30,PTR_DAT_1405f0778);
  return;
}


