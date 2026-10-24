function: FUN_140e75a70
entry: 140e75a70
body_size: 473
signature: undefined FUN_140e75a70()


void FUN_140e75a70(longlong param_1,int param_2,int param_3,int param_4,int param_5)

{
  char cVar1;
  int local_res20 [2];
  int local_30;
  int local_2c [3];
  
  local_res20[0] = param_4;
  if ((param_4 == *(int *)(param_1 + 0x20)) || (param_5 == *(int *)(param_1 + 0x24))) {
    cVar1 = FUN_140e722a0(param_1,0,param_2,local_res20);
    if (cVar1 == '\0') {
      if (param_3 <= param_5) {
        do {
          local_30 = param_3 + 1999;
          if (param_5 <= param_3 + 1999) {
            local_30 = param_5;
          }
          cVar1 = FUN_140e722a0(param_1,1,local_30,&local_30);
          if (cVar1 == '\0') {
            param_5 = local_30;
          }
          FUN_140e71e30(param_1,0xffffffff,param_3,(local_30 - param_3) + 1);
          if (param_3 < local_30 + 1) {
            param_3 = local_30 + 1;
          }
          FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
        } while (param_3 <= param_5);
      }
    }
    else {
      cVar1 = FUN_140e722a0(param_1,1,param_3,&param_5);
      if (cVar1 == '\0') {
        if (param_2 <= local_res20[0]) {
          do {
            local_2c[0] = param_2 + 1999;
            if (local_res20[0] <= param_2 + 1999) {
              local_2c[0] = local_res20[0];
            }
            cVar1 = FUN_140e722a0(param_1,0,local_2c[0],local_2c);
            if (cVar1 == '\0') {
              local_res20[0] = local_2c[0];
            }
            FUN_140e71e30(param_1,param_2,0xffffffff,(local_2c[0] - param_2) + 1);
            if (param_2 < local_2c[0] + 1) {
              param_2 = local_2c[0] + 1;
            }
            FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
          } while (param_2 <= local_res20[0]);
        }
      }
      else {
        FUN_140e722a0(param_1,0,local_res20[0],local_res20);
        FUN_140e722a0(param_1,1,param_5,&param_5);
        FUN_140e74b60(param_1,param_2,param_3,local_res20[0],param_5);
      }
    }
  }
  else {
    FUN_140e74b60(param_1,param_2,param_3,param_4,param_5);
  }
  return;
}


