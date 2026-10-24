object WorkspaceManagerDialog: TWorkspaceManagerDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgWorkspaceManager'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Manage Workspaces'
  ClientHeight = 403
  ClientWidth = 313
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ShortCutLbl: TUiLabel
    Left = 8
    Top = 232
    Height = 13
    Caption = '&Shortcut:'
    FocusControl = ShortCutEdit
  end
  object AutoLoadNameLbl: TUiLabel
    Left = 8
    Top = 280
    Height = 13
    Caption = 'On s&tartup, load:'
    FocusControl = AutoLoadNameEdit
  end
  object AutoSaveNameLbl: TUiLabel
    Left = 8
    Top = 326
    Height = 13
    Caption = 'On &exit, save as:'
    FocusControl = AutoSaveNameEdit
  end
  object ListView: TUiListView
    Left = 8
    Top = 8
    Width = 297
    Height = 185
    Columns = <
      item
        Width = 173
      end
      item
        Width = 104
      end
    >
    RowSelect = True
    TabOrder = 0
    ViewStyle = vsReport
    OnEdited = ListViewEdited
    OnEditing = ListViewEditing
    OnSelectItem = ListViewSelectItem
    OnCancelEdit = ListViewCancelEdit
  end
  object DeleteBtn: TUiBitBtn
    Left = 8
    Top = 201
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = DeleteClick
  end
  object ShortCutEdit: TUiShortCutEdit
    Left = 8
    Top = 249
    Width = 216
    Height = 21
    TabOrder = 2
    OnChange = ShortCutEditChange
  end
  object ShortCutRemoveBtn: TUiButton
    Left = 232
    Top = 249
    Caption = '&Remove'
    TabOrder = 3
    OnClick = ShortCutRemoveClick
    AutoSize = asRight
  end
  object AutoLoadNameEdit: TUiComboBox
    Left = 8
    Top = 297
    Width = 297
    Height = 21
    TabOrder = 4
    OnChange = AutoNameEditChange
  end
  object AutoSaveNameEdit: TUiComboBox
    Left = 8
    Top = 343
    Width = 297
    Height = 21
    TabOrder = 5
    OnChange = AutoNameEditChange
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 364
    Width = 313
    TabOrder = 6
    object CloseBtn: TUiCloseBtn
    end
  end
  object ListPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object DeleteItem: TUiMenuItem
      Caption = 'Delete'
      ShortCut = 46
      OnClick = DeleteClick
    end
    object RenameItem: TUiMenuItem
      Caption = 'Rename'
      ShortCut = 113
      OnClick = RenameClick
    end
  end
end
