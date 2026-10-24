function: FUN_14000dce0
entry: 14000dce0
body_size: 191
signature: undefined FUN_14000dce0()


ulonglong FUN_14000dce0(ulonglong *param_1,longlong param_2,byte param_3)

{
  undefined4 *puVar1;
  bool bVar2;
  undefined4 uVar3;
  ulonglong uVar4;
  longlong lVar5;
  ulonglong uVar6;
  
  uVar4 = (ulonglong)param_3;
  if (DAT_141c9d048 <= param_2) {
    for (; param_2 != 0; param_2 = param_2 + -1) {
      *(byte *)param_1 = param_3;
      param_1 = (ulonglong *)((longlong)param_1 + 1);
    }
    return uVar4;
  }
  if (0 < param_2) {
    uVar4 = uVar4 * 0x101010101010101;
    uVar3 = (undefined4)uVar4;
    if (0x20 < param_2) {
      *(undefined4 *)param_1 = uVar3;
      *(undefined4 *)((longlong)param_1 + 4) = uVar3;
      *(undefined4 *)(param_1 + 1) = uVar3;
      *(undefined4 *)((longlong)param_1 + 0xc) = uVar3;
      puVar1 = (undefined4 *)((longlong)param_1 + param_2 + -0x10);
      *puVar1 = uVar3;
      puVar1[1] = uVar3;
      puVar1[2] = uVar3;
      puVar1[3] = uVar3;
      uVar6 = (ulonglong)((longlong)param_1 + param_2 + -1) & 0xfffffffffffffff0;
      lVar5 = ((ulonglong)(param_1 + 2) & 0xfffffffffffffff0) - uVar6;
      do {
        puVar1 = (undefined4 *)(lVar5 + uVar6);
        *puVar1 = uVar3;
        puVar1[1] = uVar3;
        puVar1[2] = uVar3;
        puVar1[3] = uVar3;
        bVar2 = lVar5 < -0x10;
        lVar5 = lVar5 + 0x10;
      } while (bVar2);
      return uVar4;
    }
    lVar5 = param_2 + -8;
    if (lVar5 == 0 || param_2 < 8) {
                    /* WARNING (jumptable): Sanity check requires truncation of jumptable */
                    /* WARNING: Could not find normalized switch variable to match jumptable */
      switch(param_2) {
      case 0:
        goto switchD_14000dd1f_caseD_0;
      case 5:
        *(char *)((longlong)param_1 + 4) = (char)uVar4;
      case 4:
        *(undefined4 *)param_1 = uVar3;
        return uVar4;
      case 6:
        *(undefined4 *)((longlong)param_1 + 2) = uVar3;
      case 2:
        *(short *)param_1 = (short)uVar4;
        return uVar4;
      case 7:
        *(undefined4 *)((longlong)param_1 + 3) = uVar3;
      case 3:
        *(short *)((longlong)param_1 + 1) = (short)uVar4;
      case 1:
        *(char *)param_1 = (char)uVar4;
        return uVar4;
      }
    }
    else {
      if ('\b' < (char)lVar5) {
        if ('\x10' < (char)lVar5) {
          param_1[2] = uVar4;
        }
        param_1[1] = uVar4;
      }
      *(ulonglong *)((longlong)param_1 + lVar5) = uVar4;
    }
    *param_1 = uVar4;
  }
switchD_14000dd1f_caseD_0:
  return uVar4;
}


