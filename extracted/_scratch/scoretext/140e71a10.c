function: FUN_140e71a10
entry: 140e71a10
body_size: 428
signature: undefined FUN_140e71a10()


void FUN_140e71a10(longlong *param_1,undefined8 param_2,undefined8 *param_3,undefined4 param_4,
                  undefined4 param_5,undefined4 param_6,undefined4 param_7)

{
  char cVar1;
  int iVar2;
  undefined1 auStack_78 [40];
  undefined1 *local_50;
  undefined8 local_40;
  undefined8 uStack_38;
  undefined8 *local_30;
  
  local_50 = auStack_78;
  local_40 = *param_3;
  uStack_38 = param_3[1];
  cVar1 = (**(code **)(*param_1 + 0x20))(param_1);
  if (cVar1 != '\0') {
    cVar1 = (**(code **)(*param_1 + 0x48))(param_1);
    if (cVar1 != '\0') {
      FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Bc\\BcAlignLines.pas",0xef
                   );
    }
  }
  iVar2 = (**(code **)(*param_1 + 0x38))(param_1);
  if (iVar2 < 1) {
    FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Bc\\BcAlignLines.pas",0xf0);
  }
  cVar1 = (**(code **)*param_1)(param_1);
  if (cVar1 == '\x01') {
    local_30 = (undefined8 *)FUN_1400107b0(PTR_PTR_140e718c0,1);
  }
  else if (cVar1 == '\x02') {
    local_30 = (undefined8 *)FUN_1400107b0(PTR_PTR_140e70f20,1);
  }
  else {
    local_30 = (undefined8 *)FUN_1400107b0(PTR_PTR_140e71510,1);
  }
  local_30[1] = param_2;
  local_30[2] = param_1;
  *(undefined4 *)(local_30 + 3) = param_4;
  *(undefined4 *)((longlong)local_30 + 0x1c) = param_5;
  *(undefined4 *)(local_30 + 4) = param_6;
  *(undefined4 *)((longlong)local_30 + 0x24) = param_7;
  local_30[5] = local_40;
  local_30[6] = uStack_38;
  (**(code **)*local_30)(local_30);
  FUN_140010870(local_30);
  return;
}


