object OpNewFolderDialog: TOpNewFolderDialog
  HelpType = htKeyword
  HelpKeyword = 'OpNewFolder'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Create New Folder'
  ClientHeight = 123
  ClientWidth = 393
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object NameLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Name:'
    FocusControl = NameEdit
  end
  object CreateInLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'Create in:'
  end
  object PathLbl: TUiLabel
    Left = 16
    Top = 71
    Height = 13
    Caption = '%'
    ShowAccelChar = False
  end
  object NameEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 377
    Height = 21
    TabOrder = 0
    OnChange = NameEditChange
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 84
    Width = 393
    TabOrder = 1
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
