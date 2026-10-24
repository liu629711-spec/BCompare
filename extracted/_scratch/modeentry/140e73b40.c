function: FUN_140e73b40
entry: 140e73b40
body_size: 371
signature: undefined FUN_140e73b40()


void FUN_140e73b40(longlong param_1,int param_2,int param_3,int param_4,int param_5)

{
  char cVar1;
  int iVar2;
  undefined1 uVar3;
  int local_res20 [2];
  int local_30;
  int local_2c;
  
  local_res20[0] = param_4;
  if ((param_4 == *(int *)(param_1 + 0x20)) || (param_5 == *(int *)(param_1 + 0x24))) {
    uVar3 = 1;
  }
  else {
    uVar3 = 0;
  }
  do {
    local_2c = local_res20[0];
    local_30 = param_5;
    cVar1 = FUN_140e722a0(param_1,0,param_2,local_res20);
    if (cVar1 == '\0') {
      cVar1 = FUN_140e722a0(param_1,1,param_3,&param_5);
      if (cVar1 == '\0') {
        return;
      }
      iVar2 = param_3 + 199;
      if (local_30 <= param_3 + 199) {
        iVar2 = local_30;
      }
      local_30 = iVar2;
      FUN_140e722a0(param_1,1,iVar2,&local_30);
      FUN_140e71e30(param_1,0xffffffff,param_3,(local_30 - param_3) + 1);
    }
    else {
      cVar1 = FUN_140e722a0(param_1,1,param_3,&param_5);
      if (cVar1 == '\0') {
        iVar2 = param_2 + 199;
        if (local_2c <= param_2 + 199) {
          iVar2 = local_2c;
        }
        local_2c = iVar2;
        FUN_140e722a0(param_1,0,iVar2,&local_2c);
        FUN_140e71e30(param_1,param_2,0xffffffff,(local_2c - param_2) + 1);
      }
      else {
        FUN_140e733b0(param_1,param_2,param_3,&local_2c,&local_30,uVar3);
      }
    }
    if (param_2 < local_2c + 1) {
      param_2 = local_2c + 1;
    }
    if (param_3 < local_30 + 1) {
      param_3 = local_30 + 1;
    }
    FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
  } while( true );
}


