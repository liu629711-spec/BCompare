object SccOpDialog: TSccOpDialog
  BorderStyle = bsSizeable
  Caption = '%'
  ClientHeight = 277
  ClientWidth = 497
  Constraints.MinHeight = 145
  Constraints.MinWidth = 269
  OnClose = FormClose
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object CommentLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'C&omments:'
    FocusControl = CommentEdit
  end
  object CommentEdit: TUiMemo
    Left = 8
    Top = 25
    Width = 481
    Height = 188
    Anchors = [akLeft, akTop, akRight, akBottom]
    TabOrder = 0
  end
  object KeepCheckedOutEdit: TUiCheckBox
    Left = 8
    Top = 221
    Height = 17
    Anchors = [akLeft, akBottom]
    Caption = '&Keep files checked out'
    TabOrder = 1
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 238
    Width = 497
    TabOrder = 2
    SizeGripper = True
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
    object AdvancedBtn: TUiAdvancedBtn
      Caption = 'A&dvanced...'
      OnClick = AdvancedClick
    end
  end
end
