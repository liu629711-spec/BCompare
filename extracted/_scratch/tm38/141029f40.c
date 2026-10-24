function: FUN_141029f40
entry: 141029f40
body_size: 266
signature: undefined FUN_141029f40()


undefined1 FUN_141029f40(undefined8 param_1,undefined4 param_2)

{
  char cVar1;
  uint uVar2;
  longlong *plVar3;
  undefined8 uVar4;
  longlong lVar5;
  undefined1 local_11;
  longlong local_10;
  
  local_10 = 0;
  uVar2 = FUN_141029640(param_1,param_2,0);
  uVar2 = uVar2 & 0xff;
  if (uVar2 < 7) {
    if (uVar2 == 6) {
LAB_141029fd2:
      local_11 = 1;
      goto code_r0x00014102a036;
    }
    if (uVar2 != 0) {
      if (uVar2 != 1) {
        if (uVar2 == 2) goto LAB_141029fd2;
        if (uVar2 != 5) goto LAB_141029fd9;
      }
LAB_141029fcb:
      local_11 = 0;
      goto code_r0x00014102a036;
    }
  }
  else if (uVar2 != 8) {
    if (uVar2 == 9) goto LAB_141029fcb;
    if (uVar2 == 10) goto LAB_141029fd2;
    if (1 < uVar2 - 0xb) {
LAB_141029fd9:
      plVar3 = (longlong *)FUN_14102a280(param_1);
      cVar1 = (**(code **)(*plVar3 + 0x180))(*plVar3,2);
      if (cVar1 != '\0') {
        uVar4 = FUN_14102a280(param_1);
        FUN_140e686b0(uVar4,&local_10,2);
        if (local_10 != 0) {
          local_11 = 2;
          goto code_r0x00014102a036;
        }
      }
      lVar5 = FUN_141029ec0(param_1);
      if (*(char *)(lVar5 + 0x41) == '\x02') {
        local_11 = 1;
      }
      else {
        local_11 = 0;
      }
      goto code_r0x00014102a036;
    }
  }
  lVar5 = FUN_141029ec0(param_1);
  if (*(char *)(lVar5 + 0x41) == '\x02') {
    local_11 = 1;
  }
  else {
    local_11 = 0;
  }
code_r0x00014102a036:
  FUN_140013e30(&local_10);
  return local_11;
}


