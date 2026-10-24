function: FUN_1417a4fe0
entry: 1417a4fe0
body_size: 302
signature: undefined FUN_1417a4fe0()


longlong FUN_1417a4fe0(longlong param_1,char param_2,undefined8 param_3,undefined8 param_4,
                      undefined4 param_5,undefined8 param_6,undefined8 *param_7,undefined4 param_8,
                      int param_9)

{
  undefined1 *puVar1;
  longlong local_res8;
  undefined1 auStack_68 [32];
  undefined8 local_48;
  undefined4 local_40;
  undefined1 *local_30;
  
  local_30 = auStack_68;
  local_res8 = param_1;
  puVar1 = auStack_68;
  if (param_2 != '\0') {
    local_res8 = FUN_140011260(param_1,param_2);
    puVar1 = local_30;
  }
  local_30 = puVar1;
  local_40 = param_5;
  local_48 = param_4;
  FUN_1417a3570(local_res8,0,param_3,DAT_1417a5150);
  *(undefined8 *)(local_res8 + 0x14c) = *param_7;
  *(undefined8 *)(local_res8 + 0x154) = param_7[1];
  *(undefined4 *)(local_res8 + 0x15c) = param_8;
  *(undefined8 *)(local_res8 + 0x160) = param_6;
  *(int *)(local_res8 + 0x168) = param_9;
  *(bool *)(local_res8 + 0x148) = *(int *)(local_res8 + 0x15c) < param_9;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


