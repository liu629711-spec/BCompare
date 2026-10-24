function: FUN_141022630
entry: 141022630
body_size: 153
signature: undefined FUN_141022630()


longlong FUN_141022630(longlong param_1,char param_2,undefined8 param_3)

{
  undefined1 *puVar1;
  longlong local_res8;
  undefined1 auStack_58 [40];
  undefined1 *local_30;
  int local_1c;
  
  local_30 = auStack_58;
  local_res8 = param_1;
  puVar1 = auStack_58;
  if (param_2 != '\0') {
    local_res8 = FUN_140011260(param_1,param_2);
    puVar1 = local_30;
  }
  local_30 = puVar1;
  FUN_1400107b0(local_res8,0);
  *(undefined8 *)(local_res8 + 0x60) = param_3;
  local_1c = 0;
  do {
    *(undefined4 *)(local_res8 + 8 + (longlong)local_1c * 4) = 0xffffffff;
    local_1c = local_1c + 1;
  } while (local_1c != 10);
  *(undefined1 *)(local_res8 + 0x50) = DAT_141022710;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


