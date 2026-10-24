function: FUN_14102e2a0
entry: 14102e2a0
body_size: 330
signature: undefined FUN_14102e2a0()


undefined8 FUN_14102e2a0(undefined8 param_1,undefined8 param_2,undefined1 param_3,int *param_4)

{
  undefined4 uVar1;
  int iVar2;
  int iVar3;
  undefined8 uVar4;
  int iVar5;
  undefined8 local_30;
  undefined1 local_28 [4];
  int local_24;
  int local_20;
  int local_1c;
  
  local_30 = 0;
  FUN_140013e30(param_2);
  iVar5 = param_4[2];
  if (param_4[3] == 0) {
    iVar5 = iVar5 + -1;
  }
  do {
    if (iVar5 < *param_4) {
      FUN_140013e30(&local_30);
      return param_2;
    }
    uVar1 = FUN_1410305e0(param_1,iVar5);
    FUN_140528320(&local_20,uVar1,0);
    if (iVar5 == param_4[2]) {
      local_1c = param_4[3];
    }
    else {
      local_20 = local_20 + 1;
    }
    for (; *param_4 < iVar5; iVar5 = iVar5 + -1) {
      iVar2 = FUN_1410305e0(param_1,iVar5 + -1);
      iVar3 = FUN_1410305e0(param_1,iVar5);
      if (iVar2 != iVar3 + -1) break;
    }
    uVar1 = FUN_1410305e0(param_1,iVar5);
    FUN_140528320(local_28,uVar1,1);
    if (iVar5 == *param_4) {
      local_24 = param_4[1];
    }
    uVar4 = FUN_1410306c0(param_1);
    FUN_141025910(uVar4,&local_30,param_3,local_28);
    FUN_140016150(param_2,local_30);
    iVar5 = iVar5 + -1;
  } while( true );
}


