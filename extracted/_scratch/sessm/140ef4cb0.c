function: FUN_140ef4cb0
entry: 140ef4cb0
body_size: 258
signature: undefined FUN_140ef4cb0()


void FUN_140ef4cb0(longlong *param_1,undefined8 param_2)

{
  char cVar1;
  char cVar2;
  undefined4 uVar3;
  undefined8 uVar4;
  undefined1 auStack_58 [40];
  undefined1 *local_30;
  undefined8 *local_28;
  char local_19;
  
  local_30 = auStack_58;
  FUN_140e658e0(param_1,param_2);
  if ((char)param_1[7] == '\0') {
    FUN_140682f40(param_2,L"CodePageOverride");
    FUN_140682de0(param_2);
    local_19 = '\0';
    local_28 = (undefined8 *)PTR_PTR_141fb3420;
    do {
      cVar1 = local_19;
      cVar2 = (**(code **)(*param_1 + 0x180))(*param_1,local_19);
      if (cVar2 != '\0') {
        uVar4 = FUN_140ef4f30(param_1,cVar1);
        uVar3 = FUN_140683850(param_2,*local_28,0xffffffff);
        FUN_140ef3d60(uVar4,uVar3);
      }
      local_19 = local_19 + '\x01';
      local_28 = local_28 + 1;
    } while (local_19 != '\x03');
    FUN_140683120(param_2);
  }
  else {
    local_19 = '\0';
    do {
      cVar1 = local_19;
      cVar2 = (**(code **)(*param_1 + 0x180))(*param_1,local_19);
      if (cVar2 != '\0') {
        uVar4 = FUN_140ef4f30(param_1,cVar1);
        FUN_140ef3d60(uVar4,0xffffffff);
      }
      local_19 = local_19 + '\x01';
    } while (local_19 != '\x03');
  }
  return;
}


