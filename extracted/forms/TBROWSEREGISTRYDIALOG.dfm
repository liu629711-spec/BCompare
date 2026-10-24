object BrowseRegistryDialog: TBrowseRegistryDialog
  BorderStyle = bsSizeable
  Caption = 'Select Base Key'
  ClientHeight = 215
  ClientWidth = 313
  Constraints.MinHeight = 104
  Constraints.MinWidth = 185
  OnCloseQuery = FormCloseQuery
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object TreeView: TUiTreeView
    Left = 8
    Top = 8
    Width = 297
    Height = 168
    Anchors = [akLeft, akTop, akRight, akBottom]
    ReadOnly = True
    TabOrder = 0
    OnChange = TreeViewChange
    OnCollapsed = TreeViewCollapsed
    OnExpanding = TreeViewExpanding
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 176
    Width = 313
    TabOrder = 1
    SizeGripper = True
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
