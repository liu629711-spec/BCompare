function: FUN_140e61ba0
entry: 140e61ba0
body_size: 216
signature: undefined FUN_140e61ba0()


longlong * FUN_140e61ba0(longlong *param_1,longlong *param_2,undefined1 param_3)

{
  longlong lVar1;
  char cVar2;
  undefined4 uVar3;
  longlong local_20 [2];
  
  local_20[0] = 0;
  lVar1 = param_1[9];
  FUN_140014550(local_20,*(undefined8 *)(lVar1 + 0x168));
  if (local_20[0] == 0) {
    FUN_140014550(local_20,param_1[10]);
  }
  uVar3 = FUN_140e63000(param_1);
  FUN_140e63db0(lVar1,param_2,uVar3,local_20[0],0,param_3,0);
  if (*param_2 == 0) {
    if (*(longlong *)(param_1[9] + 0x168) == 0) {
      cVar2 = (**(code **)(*param_1 + 0xc0))(*param_1);
      if (cVar2 == '\0') goto code_r0x000140e61c64;
    }
    *(undefined4 *)(param_1[9] + 0x148) = 0;
  }
code_r0x000140e61c64:
  FUN_140013e30(local_20);
  return param_2;
}


