object TableSortDialog: TTableSortDialog
  Caption = 'Sort'
  ClientHeight = 265
  ClientWidth = 217
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnKeyDown = FormKeyDown
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object TopBevel: TUiBevel
    Left = 8
    Top = 32
    Width = 201
    Height = 1
    Shape = bsTopLine
  end
  object BottomBevel: TUiBevel
    Left = 8
    Top = 196
    Width = 201
    Height = 1
    Shape = bsTopLine
  end
  object HasNamesEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = 'Includes column names'
    TabOrder = 0
    OnClick = HasNamesClick
  end
  object ScrollBox: TUiScrollBox
    Left = 0
    Top = 33
    Width = 217
    Height = 162
    VertScrollBar.Tracking = True
    AutoScroll = False
    BorderStyle = bsNone
    TabOrder = 1
  end
  object NewBtn: TUiBitBtn
    Left = 8
    Top = 203
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = NewClick
  end
  object DeleteBtn: TUiBitBtn
    Left = 32
    Top = 203
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = DeleteClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 226
    Width = 217
    TabOrder = 4
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
