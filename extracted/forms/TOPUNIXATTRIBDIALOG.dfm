object OpUnixAttribDialog: TOpUnixAttribDialog
  HelpType = htKeyword
  HelpKeyword = 'OpAttrib'
  Caption = 'Attributes'
  ClientHeight = 467
  PixelsPerInch = 96
  TextHeight = 13
  object ActionPanel: TUiPanel
    Height = 201
    object ActionDescLbl: TUiLabel
      Left = 8
      Top = 29
      Width = 361
      Height = 26
      Caption = 'Check a box to set attribute on selected files.  Uncheck a box to clear attribute.'
      WordWrap = True
    end
    object OwnerLbl: TUiLabel
      Left = 8
      Top = 63
      Height = 13
      Caption = '&Owner:'
      FocusControl = OwnerEdit
    end
    object GroupLbl: TUiLabel
      Left = 136
      Top = 63
      Height = 13
      Caption = '&Group:'
      FocusControl = GroupEdit
    end
    object PermissionsLbl: TUiLabel
      Left = 264
      Top = 63
      Height = 13
      Caption = '&Permissions:'
      FocusControl = PermissionsEdit
    end
    object OwnerReadLbl: TUiLabel
      Left = 8
      Top = 109
      Height = 13
      Caption = 'O&wner:'
      FocusControl = OwnerReadEdit
    end
    object GroupReadLbl: TUiLabel
      Left = 136
      Top = 109
      Height = 13
      Caption = 'Gro&up:'
      FocusControl = GroupReadEdit
    end
    object OtherReadLbl: TUiLabel
      Left = 264
      Top = 109
      Height = 13
      Caption = 'O&ther:'
      FocusControl = OtherReadEdit
    end
    object OwnerEdit: TUiEdit
      Left = 8
      Top = 80
      Width = 120
      Height = 21
      TabOrder = 0
    end
    object GroupEdit: TUiEdit
      Left = 136
      Top = 80
      Width = 120
      Height = 21
      TabOrder = 1
    end
    object PermissionsEdit: TUiEdit
      Left = 264
      Top = 80
      Width = 120
      Height = 21
      MaxLength = 3
      TabOrder = 2
      OnChange = PermissionsEditChange
    end
    object OwnerReadEdit: TUiCheckBox
      Left = 8
      Top = 126
      Height = 17
      Caption = 'Read'
      TabOrder = 3
      OnClick = PermissionsChangedClick
    end
    object OwnerWriteEdit: TUiCheckBox
      Left = 8
      Top = 147
      Height = 17
      Caption = 'Write'
      TabOrder = 4
      OnClick = PermissionsChangedClick
    end
    object OwnerExecuteEdit: TUiCheckBox
      Left = 8
      Top = 168
      Height = 17
      Caption = 'Execute'
      TabOrder = 5
      OnClick = PermissionsChangedClick
    end
    object GroupReadEdit: TUiCheckBox
      Left = 136
      Top = 126
      Height = 17
      Caption = 'Read'
      TabOrder = 6
      OnClick = PermissionsChangedClick
    end
    object GroupWriteEdit: TUiCheckBox
      Left = 136
      Top = 147
      Height = 17
      Caption = 'Write'
      TabOrder = 7
      OnClick = PermissionsChangedClick
    end
    object GroupExecuteEdit: TUiCheckBox
      Left = 136
      Top = 168
      Height = 17
      Caption = 'Execute'
      TabOrder = 8
      OnClick = PermissionsChangedClick
    end
    object OtherReadEdit: TUiCheckBox
      Left = 264
      Top = 126
      Height = 17
      Caption = 'Read'
      TabOrder = 9
      OnClick = PermissionsChangedClick
    end
    object OtherWriteEdit: TUiCheckBox
      Left = 264
      Top = 147
      Height = 17
      Caption = 'Write'
      TabOrder = 10
      OnClick = PermissionsChangedClick
    end
    object OtherExecuteEdit: TUiCheckBox
      Left = 264
      Top = 168
      Height = 17
      Caption = 'Execute'
      TabOrder = 11
      OnClick = PermissionsChangedClick
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 348
  end
  object BtnPanel: TUiBtnPanel
    Top = 428
  end
end
