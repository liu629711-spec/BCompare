function: FUN_140e738a0
entry: 140e738a0
body_size: 660
signature: undefined FUN_140e738a0()


void FUN_140e738a0(longlong *param_1,int param_2,int param_3,int param_4,int param_5)

{
  char cVar1;
  char cVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int local_res20 [2];
  int local_2c;
  
  iVar5 = -1;
  iVar6 = -1;
  local_res20[0] = param_4;
  local_2c = param_2;
  while( true ) {
    cVar1 = FUN_140e722a0(param_1,0,local_2c,local_res20);
    cVar2 = FUN_140e722a0(param_1,1,param_3,&param_5);
    if (((cVar1 == '\0' || cVar2 == '\0') || (local_res20[0] < local_2c)) || (param_5 < param_3))
    break;
    cVar1 = FUN_140e72f30(param_1,0,local_2c);
    if (cVar1 == '\0') {
      cVar1 = FUN_140e72f30(param_1,1,param_3);
      if (cVar1 != '\0') goto LAB_140e739cc;
      if ((iVar5 < 0) && (iVar6 < 0)) {
        iVar3 = FUN_140e72e80(param_1,0,local_2c);
        iVar4 = FUN_140e72e80(param_1,1,param_3);
        if (iVar3 != iVar4) goto LAB_140e739ab;
        FUN_140e71e30(param_1,local_2c,param_3,1);
      }
      else {
LAB_140e739ab:
        if (iVar5 < 0) {
          iVar5 = local_2c;
        }
        if (iVar6 < 0) {
          iVar6 = param_3;
        }
      }
      local_2c = local_2c + 1;
      param_3 = param_3 + 1;
    }
    else {
LAB_140e739cc:
      cVar1 = FUN_140e72f30(param_1,0,local_2c);
      if (cVar1 == '\0') {
        cVar1 = (**(code **)(*(longlong *)param_1[2] + 0x28))((longlong *)param_1[2]);
        if (cVar1 != '\0') break;
        if (iVar5 < 0) {
          iVar5 = local_2c;
        }
        local_2c = local_2c + 1;
      }
      else {
        cVar1 = FUN_140e72f30(param_1,1,param_3);
        if (cVar1 == '\0') {
          cVar1 = (**(code **)(*(longlong *)param_1[2] + 0x28))((longlong *)param_1[2]);
          if (cVar1 != '\0') break;
          if (iVar6 < 0) {
            iVar6 = param_3;
          }
          param_3 = param_3 + 1;
        }
        else {
          iVar3 = FUN_140e72e80(param_1,0,local_2c);
          iVar4 = FUN_140e72e80(param_1,1,param_3);
          if (iVar3 != iVar4) break;
          if ((-1 < iVar5) || (-1 < iVar6)) {
            if (iVar5 < 0) {
              iVar5 = local_2c;
            }
            if (iVar6 < 0) {
              iVar6 = param_3;
            }
            (**(code **)(*param_1 + 8))(param_1,iVar5,iVar6,local_2c + -1,param_3 + -1);
            iVar5 = -1;
            iVar6 = -1;
          }
          FUN_140e71e30(param_1,local_2c,param_3,1);
          local_2c = local_2c + 1;
          param_3 = param_3 + 1;
        }
      }
    }
    FUN_140ddfb30(param_1[1]);
  }
  if (-1 < iVar5) {
    local_2c = iVar5;
  }
  if (-1 < iVar6) {
    param_3 = iVar6;
  }
  (**(code **)(*param_1 + 8))(param_1,local_2c,param_3,local_res20[0],param_5);
  return;
}


